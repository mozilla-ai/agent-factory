
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
    repo_url: str = Field(..., description="The GitHub repository URL evaluated.")
    score: int = Field(..., description="Overall compliance score from 0-100.")
    evaluation_details: str = Field(..., description="Human-readable summary justifying the score.")
    slack_channel_id: str = Field(..., description="Slack channel ID where the message was posted.")
    slack_message_ts: str = Field(..., description="Timestamp of the Slack message (ts).")
    db_write_status: str = Field(..., description="'success' if the INSERT executed without error, else the error message.")


# ========== System (Multi-step) Instructions ===========
INSTRUCTIONS='''
You are an automated reviewer for Mozilla AI Blueprint submissions. Follow the workflow strictly and keep your chain-of-thought private.

Step-by-step workflow:
1. Guideline acquisition – Use the `visit_webpage` tool to download the content found at https://blueprints.mozilla.ai/. Extract the explicit section that lists "Guidelines for developing top-notch Blueprints" and summarise the individual criteria you will score against. Keep these criteria in memory for later steps.
2. Repository intake – The user supplies a GitHub repository URL. Retrieve the repository README and, if available, CONTRIBUTING or docs pages via `visit_webpage`. Focus on high-level design, documentation quality, licensing, test coverage indicators, automation (CI), and openness/AI-safety best practices called for in the guidelines. You do NOT need to clone the repo; reading the public HTML pages is enough.
3. Evaluation – Compare the repository information to each guideline criterion. Assign 0-100 integer points to each criterion, then average or otherwise combine them into a single overall score out of 100. Prepare a concise yet informative textual summary explaining why the repo achieved its score, highlighting strengths and weaknesses per guideline.
4. Slack reporting –
   a. Call `slack_list_channels` to locate the channel whose name contains the substring "blueprint-submission" (case-insensitive).
   b. Compile a Slack-friendly message including the repository URL, overall score, and a bullet-point summary of the evaluation.
   c. Post this message with `slack_post_message` and capture the returned `channel_id` and `ts` (message timestamp).
5. Database logging – Insert a new row into the existing SQLite database `blueprints.db`, table `github_repo_evaluations`, with columns (`repo_url`, `score`, `details`, `created_at` defaulting to now). Use `write_query` from the SQLite MCP server.
6. Final output – Return a JSON object conforming to StructuredOutput, containing the repo URL, numeric score, evaluation details, Slack post metadata, and the SQL insertion status. All agent tool calls must succeed; if any fail, describe the error in the corresponding output field but continue with remaining steps when possible.
'''

# ========== Tools definition ===========
TOOLS = [
    visit_webpage,  # fetch webpage content for guidelines and GitHub pages
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
    """Evaluate a GitHub repository against Mozilla AI Blueprint guidelines, post the assessment to Slack, and log it into a local SQLite database."""
    input_prompt = f"Please evaluate the GitHub repository at {repo_url} following the multi-step instructions."
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
