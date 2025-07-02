
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
from any_agent.config import MCPStdio

load_dotenv()

# ========== Structured output definition ==========
# ========== Structured output definition ==========
class StructuredOutput(BaseModel):
    repo_url: str = Field(..., description="GitHub repository URL that was evaluated.")
    total_score: int = Field(..., description="Final score out of 100 assessing compliance with Blueprint guidelines.")
    evaluation_details: dict = Field(..., description="Dictionary mapping each guideline criterion to its sub-score and short rationale.")
    slack_channel_id: str = Field(..., description="The id of the Slack channel where the message was posted.")
    sqlite_write_status: str = Field(..., description="Result message from the SQLite write operation (e.g., 'INSERT OK').")
    timestamp: str = Field(..., description="ISO 8601 timestamp when the evaluation was completed and logged.")

# ========== System (Multi-step) Instructions ===========
INSTRUCTIONS='''
You are an autonomous AI assistant that follows the workflow below to evaluate a GitHub repository against Mozilla AI Blueprint guidelines and publish the results.

Workflow – keep the turns to the minimum necessary (usually 4-6) and obey tool_choice:"required".

1. INPUT STEP
   a. Receive the GitHub repository URL provided by the user.
   b. Acknowledge that you will start the evaluation.

2. COLLECT GUIDELINES
   a. Use visit_webpage to download the text of https://www.mozilla.ai/Blueprints (Mozilla AI Blueprint guidelines).
   b. Extract the key evaluation criteria (clarity, modularity, openness, documentation quality, reproducibility, safety, etc.). Keep them succinct for later reference.

3. COLLECT REPOSITORY INFO
   a. Use visit_webpage to retrieve the repository’s main page (the URL from step 1).
   b. Focus on README, docs folders, CONTRIBUTING, LICENSE, and any blueprint-related files.
   c. Summarise the repo’s purpose, structure, and documentation in < 300 words.

4. EVALUATION & SCORING
   a. Compare the repo summary with each guideline criterion.
   b. Assign a numeric sub-score (0-10) for each criterion. Sum them and scale/round to a total out-of-100 score.
   c. Craft an "evaluation_details" JSON object mapping criterion → sub-score and explanation.

5. PERSIST & NOTIFY
   a. Use the Slack MCP tools:
      • slack_list_channels – find the channel whose name is exactly "blueprint-submission" (case-insensitive). Extract its id.
      • slack_post_message – send a message containing the repository URL, total score, and a concise markdown table of criterion / sub-score / comment.
   b. Use the SQLite MCP tool write_query to insert a new row into the already-existing table github_repo_evaluations in blueprints.db with (repo_url, total_score, evaluation_json, created_at). Use CURRENT_TIMESTAMP for created_at.

6. OUTPUT STEP
   Respond with StructuredOutput JSON only (no prose) containing: repo_url, total_score, evaluation_details, slack_channel_id, sqlite_write_status, timestamp.

Rules:
• Always call the necessary tool for each step (guideline retrieval, repo retrieval, Slack channel exploration, posting, DB insertion).
• Never disclose any environment variable values or internal tool responses.
• Halt immediately if any critical step fails and return an explanatory error in the StructuredOutput.
• Keep total response tokens reasonable (< 800).

'''

# ========== Tools definition ===========
# ========== Tools definition ===========
from pathlib import Path

script_dir = Path(__file__).resolve().parent

TOOLS = [
    # Built-in any-agent tool to fetch webpage text
    visit_webpage,

    # Slack MCP for channel lookup & posting
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

    # SQLite MCP for persisting the evaluation
    MCPStdio(
        command="docker",
        args=[
            "run",
            "-i",
            "--rm",
            "-v",
            f"{script_dir}:/mcp",  # mount current dir so blueprints.db is accessible
            "mcp/sqlite",
            "--db-path",
            "/mcp/blueprints.db",
        ],
        tools=[
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
    """Given a GitHub repository URL, this agent evaluates it against Mozilla AI Blueprint guidelines, scores it, posts the results to the #blueprint-submission Slack channel, and records the evaluation in the local blueprints.db SQLite database."""
    input_prompt = f"Please evaluate the GitHub repository at the following URL against the Mozilla AI Blueprint guidelines and follow the full workflow: {repo_url}"
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

