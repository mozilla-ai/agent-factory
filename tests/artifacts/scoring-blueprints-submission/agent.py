
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
from any_agent.config import MCPStdio
from any_agent.tools import visit_webpage
import os

load_dotenv()

# ========== Structured output definition ==========
class StructuredOutput(BaseModel):
    repo_url: str = Field(..., description="The evaluated GitHub repository URL.")
    score: int = Field(..., ge=0, le=100, description="Overall score (0-100) against Blueprints guidelines.")
    evaluation_summary: str = Field(..., description="Concise explanation of the score, strengths and weaknesses.")
    slack_channel: str = Field(..., description="Slack channel id where the message was posted.")
    slack_message_ts: str = Field(..., description="Timestamp of the Slack message as returned by Slack API.")
    db_inserted: bool = Field(..., description="True if the evaluation row was successfully written to SQLite.")

# ========== System (Multi-step) Instructions ===========
INSTRUCTIONS='''
You are an autonomous software-quality reviewer that follows these exact steps to evaluate a GitHub repository against Mozilla AI’s “Blueprints – Building a top-notch Blueprint” guidelines (https://www.mozilla.ai/Bluerprints).  
The user supplies a single GitHub repository URL.

STEP 1  Fetch guidelines
  a. Visit https://www.mozilla.ai/Bluerprints with visit_webpage.
  b. Extract only the explicit quality guidelines, best-practice bullet points or numbered lists.  Summarise them concisely; call this the "guideline_summary".

STEP 2  Fetch repository material
  a. Derive the repository owner and name from the supplied URL.
  b. Attempt to download the raw README.md via https://raw.githubusercontent.com/<owner>/<repo>/main/README.md (then /master/README.md if main fails). If neither exist, fall back to visiting the normal repo web page.
  c. Extract the project description, main goals and any usage or architecture information that helps with evaluation.  Limit to ≈ 1 000 tokens.

STEP 3  Evaluate
  a. Compare the repository information with the guideline_summary.
  b. Produce an overall "score" between 0 and 100 (100 = perfect alignment).
  c. Produce a clear "evaluation_summary" (≤ 300 words) explaining strengths, weaknesses and concrete improvement advice.

STEP 4  Post to Slack
  a. Use slack_list_channels to obtain all channel names & ids.
  b. Find the channel whose name (case-insensitive, hyphens ignored) matches "blueprint-submission".  If not found, abort with an error message embedded in evaluation_summary.
  c. Construct a message in the form:
```json
{
  "repo_url": "…",
  "score": <int>,
  "evaluation_summary": "…"
}
```
  d. Post it with slack_post_message, store returned channel and message timestamp.

STEP 5  Log to SQLite
  a. Using write_query insert a new record in the already existing table github_repo_evaluations in blueprints.db with columns (repo_url, score, evaluation_text, created_at).  Use CURRENT_TIMESTAMP for created_at.
  b. On success return db_inserted = true, otherwise false and include the error message in evaluation_summary.

STEP 6  Return structured JSON output with fields specified in StructuredOutput.  Do NOT output anything else.
'''

# ========== Tools definition ===========
from any_agent.config import MCPStdio
from any_agent.tools import visit_webpage
import os

# Slack MCP – only the two tools we need
slack_mcp = MCPStdio(
    command="docker",
    args=[
        "run", "-i", "--rm",
        "-e", "SLACK_BOT_TOKEN", "-e", "SLACK_TEAM_ID",
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

# SQLite MCP – only write_query is required
sqlite_mcp = MCPStdio(
    command="docker",
    args=[
        "run", "-i", "--rm",
        "-v", f"{os.getenv('SQLITE_DB_PATH')}:/mcp/blueprints.db",
        "mcp/sqlite",
        "--db-path", "/mcp/blueprints.db",
    ],
    tools=["write_query"],
)

TOOLS = [
    visit_webpage,
    slack_mcp,
    sqlite_mcp,
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
    """Given a GitHub repository URL, the agent evaluates how well it follows Mozilla AI Blueprint guidelines, posts the result to the #blueprint-submission Slack channel and logs it in the local SQLite database."""
    input_prompt = f"Evaluate the following GitHub repository for Blueprint quality compliance: {repo_url}"
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

