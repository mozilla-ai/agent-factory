# agent.py

# good to have
# ALWAYS used
import json
import os
from pathlib import Path

from any_agent import AgentConfig, AgentRunError, AnyAgent
from any_agent.config import MCPStdio

# ADD BELOW HERE: tools made available by any-agent or agent-factory
from any_agent.tools import visit_webpage
from dotenv import load_dotenv
from fire import Fire
from pydantic import BaseModel, Field

load_dotenv()


# ========== Structured output definition ==========
class StructuredOutput(BaseModel):
    repo_url: str = Field(..., description="GitHub repository URL evaluated")
    score: int = Field(..., ge=0, le=100, description="Compliance score (0-100)")
    guideline_compliances: list[str] = Field(..., description="Guidelines satisfied by the repo")
    guideline_violations: list[str] = Field(..., description="Guidelines not satisfied")
    overall_feedback: str = Field(..., description="Concise textual feedback summary")
    slack_channel_id: str = Field(..., description="Slack channel ID used for posting")
    slack_message_ts: str = Field(..., description="Slack message timestamp returned by API")
    db_insert_success: bool = Field(..., description="True iff the SQL INSERT succeeded")


# ========== System (Multi-step) Instructions ===========
INSTRUCTIONS = """
You are an agent that evaluates a GitHub repository against Mozilla AI “Blueprints” guidelines and then records the result in two places.
Follow and tick off these steps one-by-one.  Never skip a step and never merge steps.

Step 1 – Extract guidelines
•   Fetch the page https://www.mozilla.ai/Blueprints (alias accepted: https://www.mozilla.ai/Bluerprints) with visit_webpage.
•   Read only its textual content.
•   Identify the key software-engineering guidelines that define a “top-notch blueprint”.  List them succinctly (bullet list).

Step 2 – Retrieve repository artefacts
•   The user supplied a GitHub repository URL ("repo_url").
•   Construct raw README URLs and try in order:
    1. https://raw.githubusercontent.com/<owner>/<repo>/main/README.md
    2. https://raw.githubusercontent.com/<owner>/<repo>/master/README.md
•   Visit with visit_webpage until one succeeds (200).  Save README text.
•   If both fail, fall back to the HTML repo page itself.

Step 3 – Evaluate repository
•   Compare README (and any other fetched code snippets if helpful) with the extracted guidelines.
•   Produce:
    – score (integer 0-100, higher = better compliance)
    – guideline_compliances (list of guidelines the repo meets)
    – guideline_violations (list of guidelines the repo fails or partially meets)
    – overall_feedback (concise paragraph summarising strengths & weaknesses)

Step 4 – Compose Slack message
•   Format a clear multi-line Slack message:\n```
Blueprint evaluation for <repo_url>
Score: <score>/100
Compliances: <comma-separated>
Violations: <comma-separated or “None”>
Summary: <overall_feedback>
```
•   Keep under 2 000 characters.

Step 5 – Post to Slack
•   Call slack_list_channels and find the channel whose name equals "blueprint-submission" (case-insensitive).  Extract its "id".
•   Call slack_post_message with that channel_id and the composed text.  Capture the returned "ts" (message timestamp).

Step 6 – Log to SQLite
•   Build an ISO-8601 UTC datetime string, e.g. 2024-05-02T15:04:05Z.
•   Compose SQL:
  INSERT INTO github_repo_evaluations (repo_url, score, feedback, evaluated_at)
  VALUES ('<repo_url>', <score>, '<overall_feedback>', '<iso_ts>');
•   Execute with write_query.  On success, set db_insert_success = true.

Step 7 – Final structured output
Return a JSON object that matches StructuredOutput exactly.
"""

# ========== Tools definition ===========
TOOLS = [
    # Retrieve webpages (guidelines page, README, etc.)
    visit_webpage,
    # Slack MCP – only the tools we absolutely need
    MCPStdio(
        command="docker",
        args=[
            "run",
            "-i",
            "--rm",
            "-e",
            "SLACK_BOT_TOKEN",
            "-e",
            "SLACK_TEAM_ID",
            "mcp/slack",
        ],
        env={
            "SLACK_BOT_TOKEN": os.getenv("SLACK_BOT_TOKEN"),
            "SLACK_TEAM_ID": os.getenv("SLACK_TEAM_ID"),
        },
        tools=[
            "slack_list_channels",
            "slack_post_message",
        ],
    ),
    # SQLite MCP – only the write capability we need
    MCPStdio(
        command="docker",
        args=[
            "run",
            "--rm",
            "-i",
            "--mount",
            f"type=bind,src={os.getenv('DB_PATH')},dst=/data/blueprints.db",
            "mcp/sqlite",
            "--db-path",
            "/data/blueprints.db",
        ],
        env={
            "DB_PATH": os.getenv("DB_PATH"),
        },
        tools=[
            "write_query",
        ],
    ),
]

# ========== Running the agent via CLI ===========
agent = AnyAgent.create(
    "openai",
    AgentConfig(
        model_id="o3",
        instructions=INSTRUCTIONS,
        tools=TOOLS,
        output_type=StructuredOutput,  # name of the Pydantic v2 model defined above
        model_args={"tool_choice": "auto"},
    ),
)


def main(repo_url: str):
    """Evaluate a GitHub repository against Mozilla AI Blueprint guidelines, post the result to Slack, and log it into an SQLite database."""
    input_prompt = f"Evaluate the GitHub repository at {repo_url} against Mozilla AI Blueprint guidelines."
    try:
        agent_trace = agent.run(prompt=input_prompt, max_turns=20)
    except AgentRunError as e:
        agent_trace = e.trace
        print(f"Agent execution failed: {str(e)}")
        print("Retrieved partial agent trace...")

    # Extract cost information (with error handling)
    try:
        cost_info = agent_trace.cost
        if cost_info.total_cost > 0:
            cost_msg = (
                f"input_cost=${cost_info.input_cost:.6f} + "
                f"output_cost=${cost_info.output_cost:.6f} = "
                f"${cost_info.total_cost:.6f}"
            )
            print(cost_msg)
    except Exception:

        class DefaultCost:
            input_cost = 0.0
            output_cost = 0.0
            total_cost = 0.0

        cost_info = DefaultCost()

    # Create enriched trace data with costs as separate metadata
    script_dir = Path(__file__).resolve().parent
    output_path = script_dir / "agent_eval_trace.json"

    # Prepare the trace data with costs
    trace_data = agent_trace.model_dump()
    trace_data["execution_costs"] = {
        "input_cost": cost_info.input_cost,
        "output_cost": cost_info.output_cost,
        "total_cost": cost_info.total_cost,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(trace_data, indent=2))

    return agent_trace.final_output


if __name__ == "__main__":
    Fire(main)
