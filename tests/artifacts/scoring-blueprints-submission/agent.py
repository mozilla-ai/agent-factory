
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
from tools.extract_text_from_url import extract_text_from_url
from any_agent.config import MCPStdio

load_dotenv()

# ========== Structured output definition ==========
class StructuredOutput(BaseModel):
    repository_url: str = Field(..., description="GitHub repository that was evaluated")
    guidelines_summary: str = Field(..., description="3–5 bullet summary of Mozilla Blueprint guidelines used for assessment")
    score: int = Field(..., ge=0, le=100, description="Overall compliance score (0-100)")
    evaluation_details: str = Field(..., description="Narrative evaluation covering strengths, weaknesses, and recommendations")

# ========== System (Multi-step) Instructions ===========
INSTRUCTIONS='''
You are an autonomous evaluation assistant that follows this multi-step workflow to assess a GitHub repository against Mozilla AI Blueprint guidelines and publish the results:
Step 1 – Fetch Guidelines
• Visit https://www.mozilla.ai/Bluerprints (or any 30x-redirected URL) and extract the full textual content containing the official "Blueprint guidelines".
• Summarise these guidelines in 3-5 concise bullet points so they can be referenced later.

Step 2 – Analyse Repository
• Visit the user-supplied GitHub repository URL and extract the README plus any CONTRIBUTING or GOVERNANCE files if present.
• Focus on documentation, code organisation, licensing, and best-practice signals that relate to the guidelines.

Step 3 – Evaluate & Score
• Compare the repository artefacts with the guideline summary.
• Assign an overall score from 0-100 where 100 means "perfectly follows all guidelines" and 0 means "no alignment".
• Write an evaluation paragraph covering strengths, weaknesses, and concrete improvement suggestions.

Step 4 – Produce Structured Result
Prepare a JSON object with:
  repository_url – the evaluated repo link
  guidelines_summary – your 3–5 bullet guideline digest
  score – integer 0-100
  evaluation_details – the paragraph created in Step 3

Step 5 – Post to Slack
• Use slack_list_channels to find the channel whose name contains "blueprint-submission" (case-insensitive).
• Use slack_post_message to post the JSON result to that channel. Include the repo URL and numeric score in the message text for quick scanning.

Step 6 – Log to SQLite
• Insert a new row into the existing github_repo_evaluations table in blueprints.db: (repo_url, score, evaluation_details, evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP).
• Use write_query and confirm successful insertion.

General rules
• Use the minimum set of tools provided.
• Always perform steps sequentially; do not skip or merge them.
• Output MUST conform to the StructuredOutput schema.
• Halt and return a clear error message if any mandatory tool fails.
'''

# ========== Tools definition ===========
# ========= Tools definition =========

# Slack MCP server – only the 2 tools we need
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

# SQLite MCP server – only the write_query tool
SQLITE_MCP = MCPStdio(
    command="docker",
    args=[
        "run", "-i", "--rm",
        "-v", f"{Path.cwd()}:/data",  # mount current dir so /data/blueprints.db is accessible
        "mcp/sqlite",
        "--db-path", "/data/blueprints.db",
    ],
    tools=["write_query"],
)

TOOLS = [
    visit_webpage,               # fetch guideline & repo pages
    extract_text_from_url,       # cleanly extract README and other docs
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
    """Evaluate a GitHub repository against Mozilla Blueprint guidelines, post the results to Slack, and save them to an SQLite database."""
    input_prompt = f"Evaluate the following GitHub repository against Mozilla AI Blueprint guidelines and follow all workflow steps: {repo_url}"
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

