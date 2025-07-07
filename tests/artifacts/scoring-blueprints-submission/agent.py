
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
import os

load_dotenv()

# ========== Structured output definition ==========
class StructuredOutput(BaseModel):
    repo_url: str = Field(..., description="The GitHub repository URL that was evaluated.")
    score: int = Field(..., ge=0, le=100, description="Overall adherence score to Mozilla AI Blueprint guidelines (0-100).")
    summary: str = Field(..., description="Concise narrative summary of evaluation findings.")
    guideline_violations: list[str] = Field(..., description="List of guideline points that were missed or partially met.")
    slack_channel_id: str = Field(..., description="Slack channel id where the evaluation message was posted.")
    db_write_status: str = Field(..., description="'success' or error message returned from the SQLite write operation.")

# ========== System (Multi-step) Instructions ===========
INSTRUCTIONS='''
You are a multi-step evaluation assistant.  Work through the following steps sequentially and do not skip any step.

1. Fetch Mozilla AI Blueprint guidelines
   a. Use visit_webpage to visit https://www.mozilla.ai/Bluerprints (or the most recent redirect /spelling variation). Pull only the humane-readable guideline text, ignoring navigation, ads or footer.
   b. Keep this content in memory as “Guidelines”.

2. Collect repository context (high level only – do NOT clone full repo)
   a. Accept the GitHub repository URL supplied by the user.
   b. Derive <owner>/<repo> and visit these canonical URLs, extracting text with visit_webpage:
        • https://github.com/<owner>/<repo>  (project home – description, topics, stars)
        • https://raw.githubusercontent.com/<owner>/<repo>/HEAD/README.md (README)
        • If the repo has a docs/ folder or CONTRIBUTING.md, fetch the first 1-2 of them if they exist (but stay under 8 000 tokens total).
   c. Consolidate this into “RepoContent”.

3. Evaluate the repo against the Guidelines
   a. Compare RepoContent to each guideline item.  Identify strengths, partial matches and violations.
   b. Produce a numeric score 0-100 using the rubric:
       – 90-100 excellent alignment, 75-89 good, 60-74 fair, <60 poor.
   c. Create a concise bullet list of violations / improvement points.

4. Build the structured result exactly matching the StructuredOutput schema.

5. Post the result to Slack
   a. Use slack_list_channels to find the public channel whose name contains the substring “blueprint-submission” (case-insensitive).  Keep its id.
   b. Post a well-formatted message (include repo URL, score and summary) with slack_post_message to that channel.  Record the returned channel id.

6. Log the result to SQLite
   a. Compose an INSERT statement for table github_repo_evaluations in /mcp/blueprints.db with at least (repo_url, score, summary, created_at CURRENT_TIMESTAMP).
   b. Execute using write_query.
   c. Capture success or error string.

7. Return StructuredOutput, filling:
       repo_url, score, summary, guideline_violations, slack_channel_id, db_write_status

Important rules:
• Always use the provided tools when posting to Slack or writing to SQLite.
• If any tool call fails, retry once; if it still fails set db_write_status or slack_channel_id to the error message but continue.
• Keep the entire final response within 500 tokens.
'''

# ========== Tools definition ===========
from any_agent.tools import visit_webpage
from any_agent.config import MCPStdio
import os

TOOLS = [
    # Fetch guideline and repo webpages
    visit_webpage,

    # Slack MCP – list channels & post message
    MCPStdio(
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
    ),

    # SQLite MCP – write to the existing blueprints.db file that is mounted into the container volume
    MCPStdio(
        command="docker",
        args=[
            "run", "--rm", "-i",
            "-v", "blueprints_db:/mcp",
            "mcp/sqlite",
            "--db-path", "/mcp/blueprints.db",
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
        output_type=StructuredOutput,
        model_args={"tool_choice": "required"},
    ),
)

def main(repo_url: str):
    """Evaluate a GitHub repo against Mozilla AI Blueprint guidelines, score it, then post the results to Slack and log them into a SQLite database."""
    input_prompt = f"Evaluate the following GitHub repository against the Mozilla AI Blueprint guidelines and follow all system instructions above: {repo_url}"
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

