
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

load_dotenv()

# ========== Structured output definition ==========
class StructuredOutput(BaseModel):
    notion_page_url: str = Field(..., description="URL of the newly created Notion post-mortem page.")

# ========== System (Multi-step) Instructions ===========
INSTRUCTIONS='''
You are a Post-mortem Assistant. Follow the steps strictly and keep outputs concise.

Step-1 (Input Parsing)
• Receive the variable `incident_description` from the user prompt.
• Extract key dates, teams, product names, error messages, and any unique IDs mentioned.

Step-2 (Gather Context from Sources)
A.  Notion
    • Query for pages whose titles or bodies include any keyword from `incident_description`.
    • Retrieve the first 10 matching page IDs for reference content.
B.  Monday.com
    • Get updates from the boards on Monday.com related to: `incident_description`
C.  Slack
    • Read history from the 'marketing-ops' channel for the last 7 days.
    • Filter messages that contain any keyword from `incident_description`.


DO NOT SKIP ANY OF THE ABOVE SOURCES

Step-3  (Locate Parent Page)
• Use Notion `API-post-search` to search for a page whose title equals “Post Mortems”.
• Save its `id` as `PARENT_PAGE_ID`. If multiple pages match, choose the first exact-title match.
• If no page found, STOP and reply that the parent page was not located.

Step-4  (Analysis)
• Build a chronological timeline of events across all three sources (ISO-8601 date & time).
• Determine likely root cause and contributing factors.
• List immediate impact, resolution steps, and future preventive actions.

Step-5  (Compose Report Markdown)
Create markdown with sections:
1. Summary (≤150 words)
2. Timeline (table with Time │ Source │ Event)
3. Root Cause Analysis
4. Recommendations / Next steps
Include links (Notion pages, Slack permalinks, Monday items) where available.

Step-6  (Create Notion Page)
• Use `API-post-page` with parent `PARENT_PAGE_ID`.
• Title: `Post Mortems – {incident_description[:50]}…` (truncate if >50 chars).
• Content: markdown prepared in Step-5.

Output strictly the final Structured JSON.
If any step fails irrecoverably, respond with a helpful error message.
'''

# ========== Tools definition ===========
TOOLS = [
    # Notion MCP
    MCPStdio(
        command="npx",
        args=[
          "-y",
          "@notionhq/notion-mcp-server"
        ],
        env={
            "NOTION_API_KEY": os.getenv("NOTION_API_KEY"),
            "OPENAPI_MCP_HEADERS": os.getenv("OPENAPI_MCP_HEADERS"),
        },
        tools=[
            "API-post-search",          # search pages
            "API-retrieve-a-page",      # (safety) retrieve page meta
            "API-get-block-children",   # read incident page content
            "API-post-page",            # create post-mortem page
        ],
    ),

    # Slack MCP (official)
    MCPStdio(
        command="npx",
        args=[
        "-y",
        "@zencoderai/slack-mcp-server"
        ],
        env={
            "SLACK_BOT_TOKEN": os.getenv("SLACK_BOT_TOKEN"),
            "SLACK_TEAM_ID": os.getenv("SLACK_TEAM_ID"),
        },
        tools=[
            "slack_list_channels",
            "slack_get_channel_history",
        ],
    ),

    # Monday.com MCP
    MCPStdio(
        command="npx",
        args=[
        "-y",
        "@mondaydotcomorg/monday-api-mcp",
        "-t",
        os.getenv("MONDAY_API_TOKEN"),
        "--enable-dynamic-api-tools",
        "true"
      ],
        env={
            "MONDAY_API_TOKEN": os.getenv("MONDAY_API_TOKEN"),
        },
        tools=[
            'get_board_items_by_name',
            'get_board_schema',
            'all_monday_api',
            'get_graphql_schema',
            'read_docs',
            'workspace_info',
            'all_monday_api'
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


def main(incident_description: str):
    """Given an incident description, collect relevant data from Notion, Slack, and Monday.com, analyse it, and create a structured post-mortem page under “Post Mortems” in Notion."""
    input_prompt = f"Create a post-mortem for the following incident: {incident_description}"
    try:
        agent_trace = agent.run(prompt=input_prompt, max_turns=40)
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

