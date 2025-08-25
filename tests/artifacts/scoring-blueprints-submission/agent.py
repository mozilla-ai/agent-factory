
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
    """Schema for the agent's final JSON response."""

    repo_url: str = Field(..., description="GitHub repository that was evaluated.")
    guidelines_url: str = Field(..., description="URL of the guidelines used for evaluation, always https://blueprints.mozilla.ai/ .")
    score: int = Field(..., ge=0, le=100, description="Overall score out of 100.")
    summary: str = Field(..., description="Markdown summary report that was posted to Slack and saved to SQLite.")
    slack_channel_id: str = Field(..., description="The channel ID where the report was posted.")
    sqlite_status: str = Field(..., description="Confirmation message returned from the SQLite write_query tool.")

# ========== System (Multi-step) Instructions ===========
INSTRUCTIONS='''
You are a Blueprint Quality Evaluator.
Perform the entire workflow in the ordered steps below.  NEVER skip, merge, or reorder the steps.

Step-1 – Retrieve guidelines
• Visit https://blueprints.mozilla.ai/ and extract the section that describes how to create best-in-class Blueprints.
• Summarise the key points as a bullet-list (<15 bullets).  Call this list GUIDELINES.

Step-2 – Analyse the submitted repository
• Clone or otherwise inspect the GitHub repository whose URL is supplied in the user prompt (visit the repo root, README, and whenever useful additional source files).
• Compare the repository against GUIDELINES and decide how well it follows each guideline.
• Produce a concise but detailed paragraph for every guideline explaining compliance or deviation.
• Derive a numeric SCORE between 0-100 where 100 is perfect alignment.

Step-3 – Compose the evaluation report
Prepare a Markdown report containing:
• Title line with repo URL
• Table or bullet list giving each guideline, your assessment, and any recommendations
• ‘Overall score: <SCORE>/100’ on its own line
• Short final verdict sentence (e.g. “Ready for publication” / “Needs major revisions”).

Step-4 – Post to Slack
• Use slack_list_channels to find a channel whose name contains "blueprint-submission" (case-insensitive).
• Use slack_post_message to post the Markdown report to that channel.  Save the returned channel id.

Step-5 – Persist to SQLite
• Insert a new row into the table github_repo_evaluations in the blueprints.db database using the write_query tool.
  Required columns are assumed to be: repo_url (TEXT), score (INTEGER), details (TEXT), created_at (TIMESTAMP DEFAULT CURRENT_TIMESTAMP).
  Write an INSERT statement filling repo_url, score, details (use the Markdown report text).
• Return success/failure information from the query execution.

Final-Step – Respond
Reply ONLY with a JSON object matching the StructuredOutput schema.  Do NOT include any additional keys.
'''

# ========== Tools definition ===========
TOOLS = [
    visit_webpage,  # retrieve webpage or README content
]

# The MCP server tools that are actually required for the workflow
NEEDED_MCP_TOOLS = {"slack_list_channels", "slack_post_message", "write_query"}

try:
    mcpd_client = McpdClient(api_endpoint=MCPD_ENDPOINT, api_key=MCPD_API_KEY)
    all_mcp_tools = mcpd_client.agent_tools()
    TOOLS.extend([t for t in all_mcp_tools if getattr(t, "__name__", "") in NEEDED_MCP_TOOLS])
except McpdError as e:
    print(f"Error connecting to mcpd: {e}", file=sys.stderr)

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
    """Evaluate a GitHub repository against Mozilla AI Blueprint guidelines, post the results to Slack, and archive them in SQLite."""
    input_prompt = f"Evaluate the following GitHub repository against Mozilla AI Blueprint guidelines and follow the prescribed workflow: {repo_url}"
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
