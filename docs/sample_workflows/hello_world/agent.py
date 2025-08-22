
# agent.py

# Always used imports
import json  # noqa: I001
import os
import sys
from pathlib import Path

from any_agent import AgentConfig, AgentRunError, AnyAgent
from dotenv import load_dotenv
from fire import Fire
from mcpd import McpdClient, McpdError
from pydantic import BaseModel, Field

# ADD BELOW HERE: tools made available by any-agent or agent-factory
from tools.visit_webpage import visit_webpage
from tools.extract_text_from_markdown_or_html import extract_text_from_markdown_or_html
from tools.summarize_text_with_llm import summarize_text_with_llm

load_dotenv()

# Connect to mcpd daemon for accessing available tools
MCPD_ENDPOINT = os.getenv("MCPD_ADDR", "http://localhost:8090")
MCPD_API_KEY = os.getenv("MCPD_API_KEY", None)

# ========== Structured output definition ==========
class StructuredOutput(BaseModel):
    url: str = Field(..., description="The original webpage URL provided by the user.")
    extracted_text: str = Field(
        ..., description="Plain, unformatted text extracted from the webpage, trimmed to roughly 3 000 tokens.")
    summary: str = Field(..., description="A concise paragraph summarizing the main content of the webpage.")

# ========== System (Multi-step) Instructions ===========
INSTRUCTIONS='''
You are an assistant that produces concise, accurate summaries of webpages by following this fixed, step-by-step workflow:

STEP-1 – Fetch webpage:
• Receive an input URL from the user.
• Call the `visit_webpage` tool to download the page as Markdown.
• If the tool returns an error or empty content, stop the workflow and output an appropriate message in the `summary` field.

STEP-2 – Extract plain text:
• Pass the Markdown returned in STEP-1 to `extract_text_from_markdown_or_html`, with `content_type` set to "md", to strip HTML/Markdown formatting and non-text elements.
• Trim the result to at most ~3 000 tokens (about 12 000 characters) while keeping the most informative parts.

STEP-3 – Summarize:
• Use `summarize_text_with_llm` with `summary_length="a concise paragraph"` to create a clear, self-contained summary that captures the main ideas, purpose, and key details of the page.
• The summary must not hallucinate information or include content absent from the source.

STEP-4 – Final structured output:
Return a JSON object that matches the `StructuredOutput` schema with these fields:
  • url – the original input URL.
  • extracted_text – the trimmed plain-text content from STEP-2.
  • summary – the paragraph-length summary from STEP-3 (or an error message if earlier steps failed).

General rules:
• Follow the steps in order and do not skip any.
• Use only the provided tools.
• Keep the language of the summary the same as the user’s request (default English).
• Do not expose internal reasoning or tool outputs except as specified in the schema.
'''

# ========== Tools definition ===========
TOOLS = [
    visit_webpage,                      # fetches webpage content as Markdown
    extract_text_from_markdown_or_html, # converts Markdown to plain text
    summarize_text_with_llm,            # creates a concise summary
]

try:
    mcpd_client = McpdClient(api_endpoint=MCPD_ENDPOINT, api_key=MCPD_API_KEY)
    mcp_server_tools = mcpd_client.agent_tools()
    if not mcp_server_tools:
        print("No tools found via mcpd.")
    TOOLS.extend(mcp_server_tools)
except McpdError as e:
    print(f"Error connecting to mcpd: {e}", file=sys.stderr)

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


def main(url: str):
    """Fetches a webpage, extracts its textual content, and returns a concise summary."""
    input_prompt = f"Summarize the main text content of this webpage: {url}"
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

    with output_path.open("w", encoding="utf-8") as f:
        f.write(json.dumps(trace_data, indent=2))

    return agent_trace.final_output


if __name__ == "__main__":
    Fire(main)
