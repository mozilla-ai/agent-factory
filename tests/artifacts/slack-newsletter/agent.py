
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
from any_agent.tools import search_tavily
from tools.extract_text_from_url import extract_text_from_url
from tools.summarize_text_with_llm import summarize_text_with_llm
from any_agent.config import MCPStdio

load_dotenv()

# ========== Structured output definition ==========
class StructuredOutput(BaseModel):
    newsletter_text: str = Field(..., description="The exact newsletter text that was posted to Slack.")
    word_count: int = Field(..., description="Total number of words in the newsletter (should be < 300).")
    source_links: list[str] = Field(..., description="List of all article URLs referenced in the newsletter.")
    slack_message_ts: str | None = Field(None, description="Timestamp ID returned by slack_post_message indicating successful post.")

# ========== System (Multi-step) Instructions ===========
INSTRUCTIONS='''
You are an autonomous assistant that prepares and publishes our company’s weekly AI newsletter in a concise, informal tone (max 300 words).  Follow this exact 6-step workflow and do not skip or merge steps:

Step 1 – Gather fresh links (last 7 days only)
• For each site in this list:
  - https://www.anthropic.com/news
  - https://news.mit.edu/topic/artificial-intelligence2
  - https://bair.berkeley.edu/blog/
  - https://deepmind.google/discover/blog/
• Use the search_tavily tool with the query:  "site:{DOMAIN} artificial intelligence past week" (replace {DOMAIN}).
• Collect up to 3 recent article URLs per site that were published within the last 7 days.

Step 2 – Extract article text
• For every gathered URL, call extract_text_from_url and retain the raw text.

Step 3 – Summarise
• For each article’s raw text, call summarize_text_with_llm asking for a 1-sentence informal summary (include a call-to-action style when suitable).  Keep the returned summary under 35 words.

Step 4 – Compose newsletter
• Organise the article summaries into four sections titled “Anthropic”, “MIT AI”, “BAIR”, and “DeepMind”.
• Begin with a friendly opener (e.g., “Hey team – here’s what’s hot in AI this week…”).
• Under each section, use bullet points for each article:  1-sentence summary followed by the hyperlink in parentheses.
• Ensure the entire newsletter is < 300 words and remains informal.

Step 5 – Publish to Slack
• Post the final newsletter text to the channel named "weekly-newsletter" using slack_post_message.
• The message must mention “Enjoy the read!” at the end.

Step 6 – Final JSON output
Return a JSON object matching StructuredOutput with:
• newsletter_text – the exact text posted to Slack
• word_count – integer word count
• source_links – list of all URLs cited
• slack_message_ts – the timestamp (ts) returned by slack_post_message

General rules:
• Only use the specified tools.
• Never fabricate content or sources; if no new items for a section, write “No major updates this week.”
• Respect the 300-word limit – truncating politely if needed.
'''

# ========== Tools definition ===========
TOOLS = [
    search_tavily,                  # find recent links within each site
    extract_text_from_url,          # pull full article text
    summarize_text_with_llm,        # create short informal summaries
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
            "slack_post_message",  # send the newsletter
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

def main():
    """Fetch last-week AI articles from the four specified sites, summarise them, create a <300-word informal newsletter, and post it to the #weekly-newsletter Slack channel."""
    input_prompt = f"Create this week’s company AI newsletter following the multi-step workflow."
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

