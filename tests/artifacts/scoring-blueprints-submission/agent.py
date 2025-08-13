
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
class SlackInfo(BaseModel):
    channel_id: str = Field(..., description="The Slack channel ID where the evaluation was posted.")
    message_ts: str = Field(..., description="Slack timestamp of the posted message.")

class DBWriteInfo(BaseModel):
    rows_affected: int = Field(..., description="Number of rows written to the database (should be 1).")

class StructuredOutput(BaseModel):
    repo_url: str = Field(..., description="URL of the evaluated GitHub repository.")
    score: int = Field(..., ge=0, le=100, description="Overall blueprint compliance score (0-100).")
    evaluation_summary: str = Field(..., description="Detailed narrative of the evaluation and justification of the score.")
    slack: SlackInfo = Field(..., description="Metadata about the Slack post.")
    database: DBWriteInfo = Field(..., description="Metadata about the database insertion.")

# ========== System (Multi-step) Instructions ===========
INSTRUCTIONS='''
You are an autonomous evaluation assistant that follows this strict multi-step workflow whenever you receive a GitHub repository URL from the user.

STEP-1  (Fetch guidelines)
• Visit "https://blueprints.mozilla.ai/" using the visit_webpage tool with max_length=-1 to ensure full content retrieval.
• Extract the section that outlines the official "Guidelines for writing top-notch Blueprints". Summarise these guidelines into concise bullet points that will serve as evaluation criteria.

STEP-2  (Inspect repository)
• Visit the supplied GitHub repository URL (again use visit_webpage with max_length=-1).
• Extract the README and any obvious documentation sections. Summarise the project: purpose, architecture, tooling, testing, compliance with best practices etc.

STEP-3  (Evaluate & score)
• Compare the repository summary against each guideline bullet point.
• Assign a numeric SCORE between 0 and 100 (whole integer). Provide a short justification for each guideline explaining why full / partial / no compliance was observed.
• Build an "evaluation_summary" paragraph that includes: scored breakdown, key strengths, key weaknesses, and a final recommendation.

STEP-4  (Post to Slack)
• Use slack_list_channels to obtain all channels, locate the one whose name exactly matches "blueprint-submission" (case-insensitive). Extract its channel_id.
• Compose a markdown message containing: repo URL, final SCORE/100, and evaluation_summary.
• Post this message with slack_post_message to the identified channel. Capture the response timestamp (ts).

STEP-5  (Write to SQLite)
• Insert or REPLACE a row in the existing blueprints.db table github_repo_evaluations with columns (repo_url TEXT PRIMARY KEY, score INTEGER, summary TEXT, ts TEXT, channel_id TEXT, when_evaluated DATETIME DEFAULT CURRENT_TIMESTAMP).
• Use write_query for the INSERT/REPLACE. Return number of affected rows.

STEP-6  (Return structured output)
• Produce a StructuredOutput JSON object with the fields defined in the schema. Populate slack.channel_id with the id found, slack.message_ts with the ts returned by Slack, and database.rows_affected from SQLite.

General rules:
• Obey tool use requirements strictly – do NOT fabricate IDs, always call the relevant tool.
• If any required step fails, stop and raise an error with an informative message.
• Keep replies short except for evaluation_summary.
• Never reveal internal chain-of-thought.
'''

# ========== Tools definition ===========
TOOLS = [
    # Webpage retrieval
    visit_webpage,

    # Slack MCP – only the tools required to list channels and post a message
    MCPStdio(
        command="npx",
        args=["@modelcontextprotocol/server-slack"],
        env={
            "SLACK_BOT_TOKEN": os.getenv("SLACK_BOT_TOKEN"),
            "SLACK_TEAM_ID": os.getenv("SLACK_TEAM_ID"),
        },
        tools=[
            "slack_list_channels",
            "slack_post_message",
        ],
    ),

    # SQLite MCP – only the tool required for write queries
    MCPStdio(
        command="uvx",
        args=[
            "mcp-server-sqlite",
            "--db-path",
            "blueprints.db",
        ],
        tools=["write_query"],
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
    """Evaluate a GitHub repository against Mozilla Blueprint guidelines, score it, post the results to Slack, and log the evaluation to SQLite."""
    input_prompt = f"Please evaluate this GitHub repository against Mozilla Blueprint guidelines and report the results: {repo_url}"
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
