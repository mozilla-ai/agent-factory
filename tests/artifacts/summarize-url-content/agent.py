
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
from tools.extract_text_from_url import extract_text_from_url
from tools.summarize_text_with_llm import summarize_text_with_llm

load_dotenv()

# Connect to mcpd daemon for accessing available tools
MCPD_ENDPOINT = os.getenv("MCPD_ADDR", "http://localhost:8090")
MCPD_API_KEY = os.getenv("MCPD_API_KEY", None)

# ========== Structured output definition ==========
class StructuredOutput(BaseModel):
    """Schema for the agent's final output."""

    url: str = Field(..., description="The webpage URL provided by the user.")
    extracted_text: str = Field(
        ..., description="The full plain-text content extracted from the webpage. Can be empty if extraction failed."
    )
    summary: str = Field(
        ..., description="A concise summary of the webpage content, or an error message if something went wrong."
    )

# ========== System (Multi-step) Instructions ===========
INSTRUCTIONS='''
You are an assistant that follows a clear two-step workflow to provide users with a concise summary of any webpage they supply.

1. **Extract text**
   • Use the `extract_text_from_url` tool with the provided URL.
   • If the tool returns an error string beginning with "Error", stop processing, and produce that error in `summary` while leaving `extracted_text` empty.
   • Otherwise, capture the full extracted text.

2. **Summarize text**
   • Pass the extracted text to `summarize_text_with_llm`.
   • Request "a concise paragraph" (default length). The tool returns a high-level summary.

3. **Produce structured output**
   Return a JSON object that strictly follows the `StructuredOutput` schema:
   - `url`: the original URL
   - `extracted_text`: the raw text extracted in step 1 (may be large)
   - `summary`: the summary from step 2 (or an error message if extraction failed)

Do not add any extra keys. Do not hallucinate content beyond what is in the extracted text. Limit the summary to ~150 words.
'''

# ========== Tools definition ===========
TOOLS = [
    extract_text_from_url,
    summarize_text_with_llm,
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
    """Given a webpage URL, this agent extracts the visible text and returns a concise summary."""
    input_prompt = f"Summarize the content of this webpage: {url}"
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
