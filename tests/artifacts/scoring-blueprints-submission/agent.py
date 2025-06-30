
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
from tools.extract_text_from_url import extract_text_from_url
from any_agent.config import MCPStdio

load_dotenv()

# ========== Structured output definition ==========
class StructuredOutput(BaseModel):
    repo_url: str = Field(..., description="GitHub repository that was evaluated.")
    score: int = Field(..., ge=0, le=100, description="Overall score (0-100) against Mozilla Blueprint guidelines.")
    strengths: str = Field(..., description="Key areas where the repo meets or excels guidelines.")
    weaknesses: str = Field(..., description="Key areas where the repo falls short of guidelines.")
    recommendations: str = Field(..., description="Concrete actions to improve compliance with guidelines.")
    slack_status: str = Field(..., description="'OK' if message successfully posted to Slack, else error info.")
    db_status: str = Field(..., description="'OK' if successfully written to SQLite, else error info.")

# ========== System (Multi-step) Instructions ===========
INSTRUCTIONS='''
You are a QA assistant that evaluates GitHub repositories against Mozilla AI Blueprint development guidelines. Follow this precise multi-step workflow and strictly use the available tools when indicated.

Step 1 – Fetch the guidelines
• Call extract_text_from_url on "https://www.mozilla.ai/Blueprints".
• Parse the returned text and distil the key guidelines (bullet list). Keep this list in memory for comparison.

Step 2 – Fetch the candidate repository
• You will receive a GitHub repository URL from the user.
• Call extract_text_from_url on that URL to retrieve the README and any other visible page text. This serves as the repository description for evaluation.

Step 3 – Evaluate the repository
• Compare the repository information with each guideline. Identify strengths, weaknesses, and concrete improvement suggestions.
• Assign an overall score from 0-100 (100 = fully meets or exceeds all guidelines).
• Compose a clear JSON object (see schema) containing:
  – repo_url, score, strengths, weaknesses, recommendations.

Step 4 – Post the results to Slack
• Use slack_list_channels to obtain all channels, find the one whose name exactly equals "blueprint-submission" (case-insensitive).
• If not found, create an error message; otherwise use its id.
• Post the JSON result as a message to that channel with slack_post_message. Record "OK" or the error text as slack_status.

Step 5 – Persist the results in SQLite
• Ensure a SQLite database row is written:
  – Use create_table on database blueprints.db with:
    CREATE TABLE IF NOT EXISTS github_repo_evaluations (
        repo_url TEXT PRIMARY KEY,
        score INTEGER,
        strengths TEXT,
        weaknesses TEXT,
        recommendations TEXT,
        created_at TEXT
    );
• Insert or replace the evaluation with write_query, setting created_at to current timestamp (ISO-8601). Record "OK" or the error text as db_status.

Step 6 – Final output
Return a StructuredOutput object with every field populated. Do not emit anything else.
'''

# ========== Tools definition ===========
# ensure a local directory is mounted so the SQLite container can persist the DB between runs
from pathlib import Path
import os

# create a host directory for the sqlite volume if it doesn’t exist
_db_host_dir = Path.cwd() / "blueprints_db"
os.makedirs(_db_host_dir, exist_ok=True)

TOOLS = [
    # Local python function to fetch webpage text
    extract_text_from_url,
    # Slack MCP server – only the two tools we need
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
    # SQLite MCP server – create table and insert row
    MCPStdio(
        command="docker",
        args=[
            "run",
            "-i",
            "--rm",
            "-v",
            f"{_db_host_dir}:/mcp",
            "mcp/sqlite",
            "--db-path",
            "/mcp/blueprints.db",
        ],
        tools=[
            "create_table",
            "write_query",
        ],
    ),
]

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

def run_agent(repo_url: str):
    """Evaluate a GitHub repository against Mozilla AI Blueprint guidelines, post the results to Slack, and store them in SQLite."""
    input_prompt = f"Please evaluate the following GitHub repository according to Mozilla AI Blueprint guidelines: {repo_url}"
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
    Fire(run_agent)

