
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
from any_agent.tools import visit_webpage
from any_agent.config import MCPStdio

load_dotenv()

# ========== Structured output definition ==========
class StructuredOutput(BaseModel):
    """Schema for the agent's final output."""

    repo_url: str = Field(..., description="Canonical GitHub repository URL that was evaluated.")
    score: int = Field(..., ge=0, le=100, description="Overall compliance score out of 100.")
    evaluation_details: str = Field(
        ..., description="Concise textual explanation of how the score was determined, including per-guideline remarks."
    )
    slack_channel_id: str | None = Field(
        None, description="Slack channel ID where the report was posted (None if posting failed)."
    )
    slack_message_ts: str | None = Field(
        None, description="Timestamp of the Slack message (None if posting failed)."
    )
    db_insert_success: bool = Field(
        False, description="True if the INSERT into github_repo_evaluations succeeded, otherwise False."
    )

# ========== System (Multi-step) Instructions ===========
INSTRUCTIONS='''
You are an assistant that evaluates Github repositories against the "Blueprints – How-tos for Agents" best-practice guidelines published at https://blueprints.mozilla.ai/.

Follow this multi-step workflow EXACTLY and use the available tools whenever applicable:

1. Fetch Guidelines (ONE-TIME)
   a. Use visit_webpage on https://blueprints.mozilla.ai/
   b. Extract the section that lists recommendations / principles for writing high-quality blueprints (e.g. reproducibility, transparency, modularity, evaluation, documentation, etc.). Summarise each guideline into a short bullet list that will be reused later.

2. Analyse the Submitted Repository
   a. You receive a single CLI argument called repo_url (e.g. "https://github.com/org/repo").
   b. Derive the canonical repo slug (owner/repo).
   c. Retrieve the repository’s README and (if present) docs/blueprint or agent configuration files. You may use:
      – the GitHub raw URL pattern (https://raw.githubusercontent.com/{owner}/{repo}/HEAD/README.md) with visit_webpage,
      – fallback to visiting the normal GitHub page if raw content is missing.
   d. Compare the repository content against EACH extracted guideline. For every guideline decide if it is fully met, partially met, or not met and provide one sentence justification.
   e. Compute an overall score out of 100 based on the average compliance (fully met = 100, partially met = 50, not met = 0, then mean across guidelines and round). Ensure the final score is an integer 0-100.

3. Prepare an Evaluation Report (plain-text)
   Include:
      • Repository URL
      • Overall score /100
      • Per-guideline verdicts & justifications
      • Timestamp in ISO-8601 (UTC)

4. Post to Slack #blueprint-submission
   a. Call slack_list_channels to obtain all channels.
   b. Find the channel whose name equals "blueprint-submission" (ignore the leading “#”). Extract its id → slack_channel_id.
   c. Call slack_post_message with channel=slack_channel_id and the evaluation report as the text. Capture the returned ts (message timestamp) → slack_message_ts.

5. Log to SQLite
   a. Build an INSERT statement for the existing table github_repo_evaluations with columns (repo_url TEXT, score INTEGER, details TEXT, slack_channel_id TEXT, slack_message_ts TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP).
   b. Execute the statement via write_query. If rows_affected > 0 treat the insertion as successful (db_insert_success=True), otherwise False.

6. Final Structured JSON Output (use the provided Pydantic model):
   {
     repo_url,
     score,
     evaluation_details (concise <2000 chars),
     slack_channel_id,
     slack_message_ts,
     db_insert_success
   }

CRITICAL RULES:
• Always respect tool schemas.
• NEVER reveal API keys, internal thoughts, or tool raw outputs.
• Use the tools only as needed and in the order described.
• If any step fails, set db_insert_success to False and/or omit slack ids accordingly but still output structured JSON.
'''

# ========== Tools definition ===========
TOOLS = [
    # Built-in tool to read webpages (guidelines & raw GitHub files)
    visit_webpage,

    # --- Slack MCP (official) -------------------------------------------------
    MCPStdio(
        command="npx",  # runtime
        args=[
            "@modelcontextprotocol/server-slack"  # package
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

    # --- SQLite MCP (official) -----------------------------------------------
    MCPStdio(
        command="uvx",  # runtime
        args=[
            "mcp-server-sqlite",
            "--db-path",
            "./blueprints.db",  # relative path to existing DB
        ],
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
    """Evaluate a GitHub repository against Mozilla AI Blueprint guidelines, score it, publish the result to Slack, and log it to a local SQLite database."""
    input_prompt = f"Please evaluate the GitHub repository at {repo_url} against the Mozilla AI Blueprint guidelines and follow the full workflow."
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

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(trace_data, indent=2))

    return agent_trace.final_output


if __name__ == "__main__":
    Fire(main)
