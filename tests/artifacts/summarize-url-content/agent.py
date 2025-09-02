
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
from tools.summarize_text_with_llm import summarize_text_with_llm

load_dotenv()

# Connect to mcpd daemon for accessing available tools
MCPD_ENDPOINT = os.getenv("MCPD_ADDR", "http://localhost:8090")
MCPD_API_KEY = os.getenv("MCPD_API_KEY", None)

# ========== Structured output definition ==========
class StructuredOutput(BaseModel):
    url: str = Field(..., description="The original webpage URL provided by the user.")
    summary: str = Field(..., description="A concise 4-6 sentence summary of the webpage’s main content.")

# ========== System (Multi-step) Instructions ===========
INSTRUCTIONS='''
You are an assistant that produces a concise summary of any public webpage provided by the user.
Follow this strict multi-step workflow:
1. RECEIVE exactly one URL from the user (no additional text).
2. USE the tool `visit_webpage` to download the page. The tool returns the HTML/markdown content as a string.
   • If the tool call fails, immediately return a short apology in the `summary` field and leave all other fields intact.
3. TRIM the fetched content to the first ~8 000 characters to avoid exceeding context limits while keeping the essential information.
4. USE the tool `summarize_text_with_llm` with `summary_length="short"` to produce a clear, factual, 4-6 sentence summary of the page’s main ideas. Do not add personal opinions or speculate beyond the page.
5. RETURN a JSON object that obeys the `StructuredOutput` schema strictly:
   ● url – the original URL.
   ● summary – the generated concise summary.
Do not output anything except the JSON object that conforms to the schema.
'''

# ========== Tools definition ===========
TOOLS = [
    visit_webpage,            # Fetch webpage content
    summarize_text_with_llm,  # Summarize large text with an LLM
]

try:
    mcpd_client = McpdClient(api_endpoint=MCPD_ENDPOINT, api_key=MCPD_API_KEY)
    mcp_server_tools = mcpd_client.agent_tools()
    if not mcp_server_tools:
        print("No tools found via mcpd.")
    TOOLS.extend(mcp_server_tools)
except McpdError as e:
    print(
        f"Error connecting to mcpd: {e}. If the agent doesn't use any MCP servers you can safely ignore this error",
        file=sys.stderr
    )

# ========== Running the agent via CLI ===========
agent = AnyAgent.create(
    "tinyagent",
    AgentConfig(
        model_id="openai/o3",
        instructions=INSTRUCTIONS,
        tools=TOOLS,
        output_type=StructuredOutput,  # name of the Pydantic v2 model defined above
        model_args={"tool_choice": "auto"},
    ),
)


def main(url: str):
    """Fetches a webpage and returns a concise summary of its main content."""
    input_prompt = f"Summarize the content of the following webpage: {url}"
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
