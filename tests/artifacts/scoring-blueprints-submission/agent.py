
# agent.py

# Always used imports
import json  # noqa: I001
import os
import sys
from pathlib import Path

from any_agent import AgentConfig, AgentRunError, AnyAgent
from dotenv import load_dotenv
from fire import Fire
from mcpd import McpdClient, McpdError
from pydantic import BaseModel, Field

# ADD BELOW HERE: tools made available by any-agent or agent-factory
from tools.visit_webpage import visit_webpage

load_dotenv()

# Connect to mcpd daemon for accessing available tools
MCPD_ENDPOINT = os.getenv("MCPD_ADDR", "http://localhost:8090")
MCPD_API_KEY = os.getenv("MCPD_API_KEY", None)

# ========== Structured output definition ==========
class CriterionBreakdown(BaseModel):
    criterion: str = Field(..., description="Name of the evaluated criterion, e.g. 'Documentation'.")
    score: int = Field(..., ge=0, le=20, description="Sub-score for this criterion (0-20).")
    comment: str = Field(..., description="Short explanation of the score.")

class StructuredOutput(BaseModel):
    repo_url: str = Field(..., description="GitHub repository URL that was evaluated.")
    overall_score: int = Field(..., ge=0, le=100, description="Total score out of 100.")
    breakdown: list[CriterionBreakdown] = Field(..., description="List with sub-scores and comments.")
    recommendation: str = Field(..., description="Advice or next steps for the repository author.")
    timestamp_utc: str = Field(..., description="ISO-8601 UTC timestamp when the evaluation finished.")
    slack_channel_id: str = Field(..., description="ID of the Slack channel where the message was posted.")
    slack_message_ts: str = Field(..., description="Slack message timestamp returned by slack_post_message.")
    db_insertion_status: str = Field(..., description="'success' or error message from the SQLite insertion.")

# ========== System (Multi-step) Instructions ===========
INSTRUCTIONS='''
You are a multi-step evaluation assistant that performs the following workflow:

1. INPUT HANDLING
   • Receive a single argument `repo_url` that points to a public GitHub repository.
   • Confirm the url starts with https://github.com/ . If not, abort.

2. GATHER EVALUATION MATERIAL
   a. Fetch Mozilla Blueprint guidelines:
      • Use `visit_webpage` on https://blueprints.mozilla.ai/ and extract the section that describes the quality guidelines / best-practices for Blueprints. Keep only the textual criteria you will score against.
   b. Fetch repository artefacts:
      • Use `visit_webpage` on the GitHub URL, its README, and any docs/blueprint-related files you deem useful (e.g. /blob/main/blueprint.yaml). Limit total extracted text to ~8 000 characters.

3. ASSESSMENT & SCORING
   • Derive ≤ 5 key criteria from the guidelines (e.g. Documentation quality, Security, Modularity, Re-usability, Testing).
   • For each criterion assign a sub-score (0-20) and short comment.
   • Sum to `overall_score` (0-100).

4. RESULTS OBJECT
   • Compose a JSON object with:
     - repo_url (str)
     - overall_score (int 0-100)
     - breakdown (list of {criterion, score, comment})
     - recommendation (str – next steps for the author)
     - timestamp_utc (ISO-8601 string)

5. POST TO SLACK
   • Call `slack_list_channels` (MCP-Slack) and find the channel whose `name` equals "blueprint-submission".
   • Call `slack_post_message` with that channel’s id and the JSON object prettified as the message text.
   • Record the returned `channel` and `ts` values.

6. LOG TO SQLITE
   • Build an INSERT statement for table `github_repo_evaluations` in database `blueprints.db` with columns (repo_url, overall_score, feedback_json, created_at).
   • Execute the INSERT via `write_query` (MCP-SQLite).
   • Capture success / error status.

7. FINAL OUTPUT
   • Return a structured response (see schema) containing: evaluation JSON, slack_channel_id, slack_message_ts, db_insertion_status.

GENERAL RULES
 • Keep tool usage minimal and deterministic.
 • Always obey the schema exactly.
 • If any step fails, set score to 0 and include the error in recommendation.
 • Do NOT leak internal deliberations.
'''

# ========== Tools definition ===========
TOOLS = [
    visit_webpage,  # Fetch guidelines page and GitHub repo pages
]

try:
    mcpd_client = McpdClient(api_endpoint=MCPD_ENDPOINT, api_key=MCPD_API_KEY)
    mcp_server_tools = mcpd_client.agent_tools()
    if not mcp_server_tools:
        print("No tools found via mcpd.")
    TOOLS.extend(mcp_server_tools)
except McpdError as e:
    print(
        f"Error connecting to mcpd: {e}. If the agent doesn't use any MCP servers you can safely ignore this error",
        file=sys.stderr
    )

# ========== Running the agent via CLI ===========
agent = AnyAgent.create(
    "tinyagent",
    AgentConfig(
        model_id="openai/o3",
        instructions=INSTRUCTIONS,
        tools=TOOLS,
        output_type=StructuredOutput,  # name of the Pydantic v2 model defined above
        model_args={"tool_choice": "auto"},
    ),
)


def main(repo_url: str):
    """Evaluate a GitHub repository against Mozilla Blueprint guidelines, post the results to Slack, and record them in a local SQLite database."""
    input_prompt = f"Please evaluate the following GitHub repository against Mozilla Blueprint guidelines: {repo_url}"
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
        "total_cost": cost_info.total_cost
    }

    with output_path.open("w", encoding="utf-8") as f:
        f.write(json.dumps(trace_data, indent=2))

    return agent_trace.final_output


if __name__ == "__main__":
    Fire(main)
