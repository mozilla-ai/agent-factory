
# agent.py

# good to have
import os

# ALWAYS used
import json
from pathlib import Path
from dotenv import load_dotenv
from any_agent import AgentConfig, AnyAgent, AgentRunError
from pydantic import BaseModel, Field
from fire import Fire

# ADD BELOW HERE: tools made available by any-agent or agent-factory
from pathlib import Path
from any_agent.tools import visit_webpage
from any_agent.config import MCPStdio

load_dotenv()

# ========== Structured output definition ==========
class StructuredOutput(BaseModel):
    repo_url: str = Field(..., description="URL of the evaluated GitHub repository.")
    guidelines_summary: str = Field(..., description="Concise summary of Mozilla AI Blueprint guidelines used for evaluation.")
    evaluation_summary: str = Field(..., description="Detailed explanation of how the repository adheres to or diverges from the guidelines.")
    score: int = Field(..., ge=0, le=100, description="Overall adherence score (0-100).")
    slack_channel_id: str = Field(..., description="ID of the Slack channel where the evaluation message was posted.")
    sqlite_write_status: str = Field(..., description="Result of logging the evaluation to SQLite, e.g., 'success' or error string.")
    timestamp_utc: str = Field(..., description="ISO-8601 UTC timestamp when the evaluation was performed.")

# ========== System (Multi-step) Instructions ===========
INSTRUCTIONS='''
You are an autonomous evaluation assistant that follows this exact multi-step workflow to assess a GitHub repository against Mozilla AI Blueprint guidelines, post the results to Slack, and log them to SQLite.

Step-by-Step Workflow
1. Fetch Guidelines
   a. Use visit_webpage to download the content at https://www.mozilla.ai/Bluerprints (Mozilla AI Blueprint guidelines).
   b. Extract and concisely summarise the key criteria (max 200 words).  
2. Inspect Repository
   a. Visit the supplied GitHub repository URL (root page).  
   b. Extract the README and any obvious CONTRIBUTING or docs pages if they exist on the landing page. Summarise the repo’s purpose, scope and development practices (max 150 words).  
3. Evaluate & Score
   a. Compare the repository characteristics with each guideline criterion.  
   b. Provide a clear evaluation summary explaining strengths, weaknesses and missing items.  
   c. Produce an overall integer score 0-100 (higher = better adherence).  
4. Post to Slack
   a. Use slack_list_channels to find the public channel whose name contains the string “blueprint-submission”; retrieve its id.  
   b. Compose a well-formatted message (markdown) containing: repo URL, score, short summary, and a link to the full evaluation (the long summary can be included inline if < 3500 chars).  
   c. Post the message with slack_post_message to that channel, capturing the returned channel_id.  
5. Log to SQLite
   a. Insert a row into the existing table github_repo_evaluations in blueprints.db via write_query. Columns assumed: repo_url TEXT, score INTEGER, evaluation_summary TEXT, timestamp_utc TEXT.  
   b. If insertion succeeds, note “success”; otherwise note the error string.  
6. Final Structured Output
   Return a JSON object that follows the StructuredOutput model exactly.

General Behaviour Rules
• Think through each step; call tools only when necessary.
• Never invent data or guess tool outputs.
• On any fatal error, still return StructuredOutput with best info available and an explanatory evaluation_summary.
• Keep tokens economical.
• All date/times must be in ISO-8601 UTC (e.g., 2024-05-18T14:33:00Z).
'''

# ========== Tools definition ===========
# Compute path to project root for volume mounting
script_dir = Path(__file__).resolve().parent

SLACK_MCP = MCPStdio(
    command="docker",
    args=[
        "run", "-i", "--rm",
        "-e", "SLACK_BOT_TOKEN",
        "-e", "SLACK_TEAM_ID",
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
)

SQLITE_MCP = MCPStdio(
    command="docker",
    args=[
        "run", "-i", "--rm",
        "-v", f"{script_dir}:/work",
        "mcp/sqlite",
        "--db-path", "/work/blueprints.db",
    ],
    tools=[
        "write_query",
    ],
)

TOOLS = [
    visit_webpage,  # Extract guidelines & repo content
    SLACK_MCP,
    SQLITE_MCP,
]

 

# ========== Running the agent via CLI ===========
agent = AnyAgent.create(
    "openai",
    AgentConfig(
        model_id="o3",
        instructions=INSTRUCTIONS,
        tools=TOOLS,
        output_type=StructuredOutput,
        model_args={"tool_choice": "required"},
    ),
)

def main(repo_url: str):
    """Evaluate a GitHub repository against Mozilla AI Blueprint guidelines, post the results to Slack, and store them in the local SQLite database."""
    input_prompt = f"Assess the following GitHub repository against Mozilla AI Blueprint guidelines and follow all workflow steps: {repo_url}"
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

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(trace_data, indent=2))

    return agent_trace.final_output

if __name__ == "__main__":
    Fire(main)

