
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
class EvaluationCriterion(BaseModel):
    criterion: str = Field(..., description="The guideline being assessed, e.g. 'Comprehensive README'.")
    score: int = Field(..., ge=0, le=10, description="Score (0-10) awarded for this criterion.")
    comments: str = Field(..., description="Brief justification for the score.")

class StructuredOutput(BaseModel):
    repo_url: str = Field(..., description="GitHub repository URL that was evaluated.")
    total_score: int = Field(..., ge=0, le=100, description="Total score out of 100.")
    summary: str = Field(..., description="Overall one-paragraph assessment.")
    evaluation_breakdown: list[EvaluationCriterion] = Field(
        ..., description="Per-criterion breakdown including comments.")
    slack_channel_id: str = Field(..., description="ID of the Slack channel where the result was posted.")
    db_insert_success: bool = Field(..., description="True if INSERT into SQLite succeeded, else False.")

# ========== System (Multi-step) Instructions ===========
INSTRUCTIONS='''
You are an autonomous evaluator that follows this strict multi-step workflow for every run. Your goal is to review an incoming GitHub repository with respect to Mozilla’s Blueprint development guidelines and then record and announce your verdict.

Step-1  Fetch Guidelines
• Use visit_webpage to retrieve https://blueprints.mozilla.ai/ . Extract only the explicit checklist / best-practice guidance for writing top-notch Blueprints. Summarise these guidelines into numbered evaluation criteria (max 10) that you will later grade against.

Step-2  Inspect the Repository
• Receive the repo_url from the user.
• Collect the repository’s README, LICENSE and the top-level file list. If a README link is not obvious, attempt the raw.githubusercontent.com URL in both main and master branches.
• Summarise the repo’s purpose, structure, and any blueprint-related files (.yaml, blueprint.md, etc.).

Step-3  Score the Repo
• For each criterion generated in Step-1 assign an integer score 0-10 and write 1-2 sentence justification.
• Sum the criterion scores to obtain total_score out of 100.
• Craft a short overall summary highlighting major strengths and weaknesses.

Step-4  Prepare the Structured Result
Prepare a JSON object matching the StructuredOutput schema that contains: repo_url, total_score, evaluation_breakdown (list of {criterion, score, comments}), summary.

Step-5  Post to Slack
• Use slack_list_channels to locate the public channel whose name exactly equals "blueprint-submission" (case-insensitive). Retrieve its id. If not found, abort with a clear error message.
• Use slack_post_message to post the JSON result (pretty-printed) to that channel. Save the returned channel_id.

Step-6  Persist to SQLite
• Use write_query (SQLite MCP) to insert a new row into the table github_repo_evaluations inside blueprints.db. The table has at least these columns: repo_url TEXT, total_score INTEGER, summary TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP.
• Build an INSERT statement using ? placeholders and the collected data.
• Capture whether the insertion succeeded (True / False).

Strict rules:
• Always comply with tool argument requirements.
• Never output anything other than the final JSON structured result.
• Abort early with an explanatory message if any critical step fails (e.g., channel not found, DB error).
'''

# ========== Tools definition ===========
TOOLS = [
    visit_webpage,  # Used to fetch guidelines and raw repo assets
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
    """Evaluate a GitHub repository against Mozilla Blueprint guidelines, assign a score, post the result to the #blueprint-submission Slack channel, and log it in the blueprints.db SQLite database."""
    input_prompt = f"Please evaluate the following GitHub repository: {repo_url}"
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
