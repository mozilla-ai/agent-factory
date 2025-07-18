
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
from any_agent.tools import search_tavily, visit_webpage
from tools.summarize_text_with_llm import summarize_text_with_llm
from any_agent.config import MCPStdio

load_dotenv()

# ========== Structured output definition ==========
class StructuredOutput(BaseModel):
    newsletter_text: str = Field(..., description="The full newsletter content that was posted to Slack.")
    word_count: int = Field(..., description="Total number of words in the newsletter text.")
    posted: bool = Field(..., description="True if the Slack post succeeded, else False.")
    channel_id: str | None = Field(None, description="Slack channel ID where the newsletter was posted.")
    message_ts: str | None = Field(None, description="Slack message timestamp of the posted newsletter.")
    sources: list[str] = Field(..., description="List of source article URLs referenced in the newsletter.")

# ========== System (Multi-step) Instructions ===========
INSTRUCTIONS='''
You are an autonomous newsletter assistant.  Follow this precise multi-step workflow:

1. Establish the current date (today) and calculate the date 7 days ago (inclusive).
2. For EACH of the four given websites
   • https://www.anthropic.com/news
   • https://news.mit.edu/topic/artificial-intelligence2
   • https://bair.berkeley.edu/blog/
   • https://deepmind.google/discover/blog/
   perform a focused web search limited to that domain for articles published within the last week.
   – Use search_tavily with a query like:
     "site:{domain} artificial intelligence after:{yyyy-mm-dd}" where the after date is 7 days ago.
   – Collect up to 3 of the most relevant, non-duplicate URLs per site (skip if none are recent).
3. Visit each selected URL with visit_webpage to retrieve its full content in Markdown.
4. Summarise each article to 1–2 informal sentences (≈30 words) using summarize_text_with_llm.  Preserve the factual information, keep the tone friendly, and capture the key takeaway.  Return a tuple (summary, url).
5. Group the summaries by source site in this order and label each section with the organisation’s name:
   “Anthropic”, “MIT AI”, “Berkeley BAIR”, “Google DeepMind”.  Within a section, list bullet points (–) in the same order you processed them.  Add the hyperlink immediately after each bullet.
6. Assemble all sections into a single newsletter headed: "📢 Weekly AI Round-Up (<today’s ISO date>)".  Ensure the total body (everything after the heading) is UNDER 300 words.  Keep an upbeat, conversational style.
7. Count words to confirm <300.  If over, shorten individual bullet phrases rather than deleting entire points.
8. Post the final newsletter text to the Slack public channel named “weekly-newsletter”.  
   – First call slack_list_channels, find the channel whose name exactly matches “weekly-newsletter” (case-insensitive).  Retrieve its id.
   – Then call slack_post_message with that channel id and the newsletter text.
   – On success capture the message timestamp.
9. Produce a structured JSON response with:
   newsletter_text  (the exact posted newsletter),
   word_count       (int),
   posted           (bool true if Slack post succeeded),
   channel_id,      (Slack id),
   message_ts,      (Slack timestamp),
   sources          (list of all URLs referenced).

Strictly follow the steps, use only the authorised tools, do not fabricate information, and never exceed 300 words in the newsletter.
'''

# ========== Tools definition ===========
from any_agent.tools import search_tavily, visit_webpage
from tools.summarize_text_with_llm import summarize_text_with_llm
from any_agent.config import MCPStdio
import os

TOOLS = [
    search_tavily,           # find recent articles
    visit_webpage,           # fetch article content
    summarize_text_with_llm, # LLM summarisation
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

def main(company_name: str):
    """Generate a concise (<300 words) weekly AI-news newsletter for the given company, drawn from four specified research-organisation sites, and post it to the Slack channel “weekly-newsletter”."""
    input_prompt = f"Create a weekly AI newsletter for {company_name}."
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

