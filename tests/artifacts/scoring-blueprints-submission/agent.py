
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


load_dotenv()

# ========== Structured output definition ==========
class StructuredOutput(BaseModel):
    repo_url: str = Field(..., description="The GitHub repository that was evaluated.")
    score: int = Field(..., description="Overall compliance score (0–100).")
    guidelines_feedback: str = Field(..., description="Detailed per-guideline feedback.")
    summary: str = Field(..., description="One-paragraph executive summary of the evaluation.")
    timestamp_utc: str = Field(..., description="ISO-8601 UTC timestamp when the evaluation finished.")
    slack_channel_id: str | None = Field(None, description="ID of the blueprint-submission channel used.")
    slack_message_ts: str | None = Field(None, description="Slack timestamp of the posted message.")
    db_write_status: str | None = Field(None, description="Result of the SQLite INSERT (e.g. 'success' or error text).")

# ========== System (Multi-step) Instructions ===========
INSTRUCTIONS='''
You are a multi-step evaluation assistant for Mozilla AI Blueprint submissions.
Follow these steps strictly and stop if any step fails:

1. Guidelines acquisition
   a. Visit https://www.mozilla.ai/Blueprints (or the redirected page) with the visit_webpage tool.
   b. Extract the main textual guidelines on how to produce high-quality Blueprints. Summarise them into a concise numbered list (≤ 10 items). This will be referred to as "Guideline List".

2. Repository inspection
   a. Visit the GitHub repository URL supplied by the user (normally the root page shows the README).
   b. Capture essential information: repository name, README text, primary programming language(s), stars, last commit date and any CONTRIBUTING / docs that appear on the root page. Put this into a short markdown block called "Repo Snapshot".

3. Assessment & scoring
   a. Compare the Repo Snapshot against each item of the Guideline List.
   b. Provide detailed feedback for every guideline stating how well the repo satisfies it ("Meets / Partially / Fails" with 1–2 sentence justification).
   c. Derive an overall score from 0–100 (integer). Use a transparent rubric: start at 100 and subtract equal penalties for each shortcoming; major violations subtract more.

4. Compose Structured Result
   Produce a JSON object that matches the StructuredOutput schema with fields:
     • repo_url
     • score
     • guidelines_feedback (detailed per guideline)
     • summary
     • timestamp_utc (ISO-8601)

5. Post to Slack
   a. Call slack_list_channels to retrieve channel metadata.
   b. Find the public channel whose name (lower-cased) is "blueprint-submission". Extract its id.
   c. Post a human-readable summary containing repo URL, score and a short verdict plus link back to the repo via slack_post_message.

6. Log to SQLite
   a. Use describe_table on github_repo_evaluations to learn the exact column names.
   b. Compose an INSERT that stores at minimum (repo_url, score, feedback, created_at). Use write_query to execute it.

7. Final answer
   Return the StructuredOutput JSON. Also include slack_channel_id, slack_message_ts and db_write_status inside the JSON so that the calling program can verify success.

General rules:
• Always prefer existing tools over reasoning where possible.
• If any tool call fails, explain the failure in the corresponding field and set score to 0.
• Keep the overall conversation within 1000 tokens.
'''

# ========== Tools definition ===========
# ---- Tool configuration ----
from any_agent.config import MCPStdio

# Path to the local SQLite database
script_dir = Path(__file__).resolve().parent
DB_HOST_PATH = str((script_dir / "blueprints.db").resolve())

TOOLS = [
    # Built-in any-agent tool for fetching webpage content
    visit_webpage,

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

    # SQLite MCP server – describe table & write query only
    MCPStdio(
        command="docker",
        args=[
            "run",
            "--rm",
            "-i",
            "-v",
            f"{DB_HOST_PATH}:/mcp/blueprints.db",
            "mcp/sqlite",
            "--db-path",
            "/mcp/blueprints.db",
        ],
        tools=[
            "describe_table",
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
    """Given a GitHub repository URL, this agent evaluates it against Mozilla AI Blueprint guidelines, posts the results to the #blueprint-submission Slack channel, logs the evaluation to the local blueprints.db database, and returns a structured JSON report."""
    input_prompt = f"Please evaluate the following GitHub repository against Mozilla AI Blueprint guidelines and perform the full workflow described in your system instructions. Repository URL: {repo_url}"
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

