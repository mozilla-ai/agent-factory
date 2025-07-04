
# agent.py

# good to have
import os

# ALWAYS used
from pathlib import Path
from dotenv import load_dotenv
from any_agent import AgentConfig, AnyAgent, AgentRunError
from pydantic import BaseModel, Field
from fire import Fire

# ADD BELOW HERE: tools made available by any-agent or agent-factory
from any_agent.tools import visit_webpage
from tools.review_code_with_llm import review_code_with_llm
from any_agent.config import MCPStdio

load_dotenv()

# ========== Structured output definition ==========
class StructuredOutput(BaseModel):
    repo_url: str = Field(..., description="The GitHub repository URL that was evaluated.")
    score: int = Field(..., description="Overall compliance score from 0 to 100.")
    evaluation_summary: str = Field(..., description="Detailed reasoning on how the score was determined with respect to the Mozilla Blueprints guidelines.")
    slack_channel_id: str = Field(..., description="Slack channel id where the result was posted.")
    slack_message_ts: str = Field(..., description="Timestamp of the Slack message that was posted.")
    db_write_status: str = Field(..., description="Status message returned by the SQLite write_query tool.")

# ========== System (Multi-step) Instructions ===========
INSTRUCTIONS='''
You are an autonomous agent tasked with evaluating GitHub repositories against Mozilla AI Blueprint development guidelines located at https://www.mozilla.ai/Blueprints.

Follow this strict multi-step workflow – do not skip steps and always keep internal notes to a minimum.

Step-1 ‑ Retrieve Guidelines
• Use `visit_webpage` on https://www.mozilla.ai/Blueprints to obtain the most up-to-date list of guidelines and best practices for high-quality blueprints.
• Summarize the key checkpoints that will later be used for scoring.

Step-2 ‑ Retrieve Repository Context
• The user provides a GitHub repository URL. Derive the owner/repo slug.
• Attempt to download the repo’s README (https://raw.githubusercontent.com/<owner>/<repo>/HEAD/README.md). 
• If the README is missing, fall back to the repository HTML page.
• In addition, fetch any CONTRIBUTING.md and docs/overview.md if they exist (use the same raw URL pattern).
• Combine all successfully fetched texts into a single corpus called `repo_context`.

Step-3 ‑ Evaluate Repository
• Feed BOTH `repo_context` and the list of guideline checkpoints to the `review_code_with_llm` tool.
• Ask it to produce:  
  – a short strengths & weaknesses analysis  
  – a checklist indicating whether each guideline is satisfied (yes/no + short note)  
  – an overall score from 0-100 where 100 means perfect compliance.
• Store the returned analysis as `evaluation_summary` and `score` variables.

Step-4 ‑ Post Result to Slack
• Use `slack_list_channels` to retrieve public channels. Find the channel whose name matches “blueprint-submission” (case-insensitive).
• Use `slack_post_message` to post a message to that channel. The message MUST include: repository URL, score, and a concise bulleted version of the evaluation summary.
• Capture `channel_id` and `ts` (message timestamp) returned by the post operation.

Step-5 ‑ Persist Result to SQLite
• Compose an INSERT statement for the table `github_repo_evaluations` with columns (repo_url TEXT, score INTEGER, summary TEXT, slack_channel_id TEXT, slack_message_ts TEXT, evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP).
• Use `write_query` to execute the INSERT.
• Capture the success/failure message returned.

Step-6 ‑ Final JSON Output
Return a JSON object of type StructuredOutput with:
    repo_url, score, evaluation_summary, slack_channel_id, slack_message_ts, db_write_status.
Be sure the JSON strictly conforms to the Pydantic schema. 
If any blocking error occurs at any step, still produce StructuredOutput with available information and a short explanation in evaluation_summary, and set score = 0.
'''

# ========== Tools definition ===========
TOOLS = [
    # --- Category b: any-agent built-in tools ---
    visit_webpage,

    # --- Category a: Python function tools ---
    review_code_with_llm,

    # --- MCP server for Slack ---
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

    # --- MCP server for SQLite ---
    MCPStdio(
        command="docker",
        args=[
            "run",
            "-i",
            "--rm",
            "-v",
            f"{os.getenv('BLUEPRINTS_DB_PATH')}:/mcp/blueprints.db",
            "mcp/sqlite",
            "--db-path",
            "/mcp/blueprints.db",
        ],
        env={},
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
        output_type=StructuredOutput,
        model_args={"tool_choice": "required"},
    ),
)

def main(repo_url: str):
    """Evaluate a GitHub repository against Mozilla AI Blueprint guidelines, post the results to Slack, and log them in an SQLite database."""
    input_prompt = f"Evaluate the following GitHub repository against the Mozilla Blueprints guidelines and report the results: {repo_url}"
    try:
        agent_trace = agent.run(prompt=input_prompt, max_turns=20)
    except AgentRunError as e:
        agent_trace = e.trace
        print(f"Agent execution failed: {str(e)}")
        print("Retrieved partial agent trace...")

    script_dir = Path(__file__).resolve().parent
    output_path = script_dir / "agent_eval_trace.json"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(agent_trace.model_dump_json(indent=2))

    return agent_trace.final_output

if __name__ == "__main__":
    Fire(main)

