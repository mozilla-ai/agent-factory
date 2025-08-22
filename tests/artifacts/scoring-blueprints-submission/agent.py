
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
class StructuredOutput(BaseModel):
    """Schema for the agent's final output."""

    repo_url: str = Field(..., description="GitHub repository that was evaluated")
    guidelines: list[str] = Field(..., description="Short list of extracted Blueprint guidelines used in the assessment")
    score: int = Field(..., ge=0, le=100, description="Numeric score out of 100")
    evaluation_details: str = Field(..., description="Detailed analysis referencing how the repo meets or fails each guideline")
    improvement_plan: str = Field(..., description="Concrete recommendations for improving adherence to the guidelines")
    slack_channel_id: str = Field(..., description="ID of the Slack channel used for posting the evaluation")
    slack_message_ts: str = Field(..., description="Timestamp of the Slack message that was posted")
    db_insertion_status: str = Field(..., description="Confirmation message or error string from SQLite INSERT operation")

# ========== System (Multi-step) Instructions ===========
INSTRUCTIONS='''
You are a code-review assistant evaluating GitHub repositories against Mozilla Blueprint guidelines.
Follow this precise multi-step workflow for EVERY user prompt:

STEP 1 – Fetch Guidelines
1. Use visit_webpage to download https://blueprints.mozilla.ai/ .
2. Extract the sections that describe "Blueprint best-practices / guidelines". Summarise the key points into a numbered list (5-10 bullets maximum).

STEP 2 – Analyse Repository
3. Visit the GitHub repository URL supplied by the user. Prioritise the README, CONTRIBUTING, docs folder and root-level configuration files.
4. Identify evidence that addresses each guideline (or violations / missing pieces).

STEP 3 – Score & Recommendations
5. Allocate a score out of 100.   • Start from 100 then deduct points proportionally for every unmet guideline, weighting more-important guidelines higher.  • Explain scoring rationale.
6. Produce a concise improvement plan listing concrete actions the author could take.

STEP 4 – Structured Output
7. Build a StructuredOutput instance with: repo_url, guidelines, score, evaluation_details (markdown), improvement_plan, slack_channel_id, slack_message_ts, db_insertion_status.

STEP 5 – Slack Publication
8. Call slack_list_channels (from Slack MCP) and find the channel whose name includes "blueprint-submission" (case-insensitive). Save its id.
9. Post the evaluation summary (repo URL, score, top recommendations) to that channel using slack_post_message. Save the message ts.

STEP 6 – Log to SQLite
10. Insert a row into table github_repo_evaluations in blueprints.db via write_query (SQLite MCP). Minimum columns expected: repo_url TEXT, score INT, evaluation TEXT, created_at defaults CURRENT_TIMESTAMP. Use parameterised INSERT to avoid SQL injection.
11. Confirm the row was written (rowcount > 0) and record status.

Rules
• Always execute the steps in order. Abort if any critical step fails and report the error inside evaluation_details.
• All external actions (web visits, Slack, SQLite) MUST be done with the provided tools only – never with direct HTTP requests or internal libraries.
• Keep LLM reasoning internal; final agent reply MUST be the JSON StructuredOutput only.
'''

# ========== Tools definition ===========
TOOLS = [
    visit_webpage,  # fetches webpage content – used for guidelines and GitHub repo
]

try:
    mcpd_client = McpdClient(api_endpoint=MCPD_ENDPOINT, api_key=MCPD_API_KEY)
    mcp_server_tools = mcpd_client.agent_tools()
    if not mcp_server_tools:
        print("No tools found via mcpd.")
    TOOLS.extend(mcp_server_tools)
except McpdError as e:
    print(f"Error connecting to mcpd: {e}", file=sys.stderr)

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
    """Evaluate a GitHub repository against Mozilla Blueprint guidelines, post results to Slack #blueprint-submission and log them into the blueprints.db SQLite database."""
    input_prompt = f"Please evaluate the following GitHub repository against Mozilla Blueprint guidelines and report the results: {repo_url}"
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
