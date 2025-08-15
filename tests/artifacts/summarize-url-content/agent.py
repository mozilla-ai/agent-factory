
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
        ..., description="Cleaned, plain-text content extracted from the webpage (may be truncated)."
    )
    summary: str = Field(..., description="A concise paragraph summarising the webpage content.")

# ========== System (Multi-step) Instructions ===========
INSTRUCTIONS='''
You are an expert assistant that summarizes the content of webpages.  Follow this STRICT multi-step workflow and always return JSON matching the StructuredOutput schema.

STEP-BY-STEP WORKFLOW
1. The user provides a single web URL.
2. Call the `extract_text_from_url` tool with that URL.
   2.1 If the returned string starts with "Error", immediately produce StructuredOutput with:
        • url  = the given URL
        • extracted_text = ""
        • summary = the full error message.
        • END.
3. Clean the extracted text:
   • Remove leading/trailing whitespace.
   • If length > 20,000 characters, truncate to the first 20,000 characters (to keep within token limits).
4. Call `summarize_text_with_llm` with the cleaned text and the instruction "a concise paragraph (≈100–150 words)".
5. Produce the final StructuredOutput JSON object with:
   • url  – the original URL
   • extracted_text – the (possibly truncated) text used for summarisation
   • summary – the paragraph generated in step 4
6. Output ONLY the JSON representation of StructuredOutput—no extra keys, no markdown, no commentary.
'''

# ========== Tools definition ===========
# List of tools the agent can invoke
tools_list = [
    extract_text_from_url,
    summarize_text_with_llm,
]

TOOLS = tools_list

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
    """Given a web URL, this agent extracts the page’s text and returns a concise paragraph summary together with the extracted text."""
    input_prompt = f"Provide a concise summary of the content at this URL: {url}"
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
