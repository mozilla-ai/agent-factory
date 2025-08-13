# agent.py

# good to have

# ALWAYS used
import json
from pathlib import Path

from any_agent import AgentConfig, AgentRunError, AnyAgent

# ADD BELOW HERE: tools made available by any-agent or agent-factory
from any_agent.tools import visit_webpage
from dotenv import load_dotenv
from fire import Fire
from pydantic import BaseModel, Field

load_dotenv()


# ========== Structured output definition ==========
class StructuredOutput(BaseModel):
    url: str = Field(..., description="The original webpage URL provided by the user.")
    summary: str = Field(..., description="A concise English summary (≈100–150 words) of the main page content.")


# ========== System (Multi-step) Instructions ===========
INSTRUCTIONS = """
You are an assistant that follows this concise multi–step workflow to produce a high-quality summary for any public webpage:

STEP-BY-STEP PLAN
1. Receive a webpage URL from the user.
2. Use the `visit_webpage` tool to download the page in Markdown.
3. Parse the Markdown and extract the primary textual content. Ignore navigation, ads, footers, scripts or non-informational elements. Keep focus on headings and paragraphs that convey the core message.
4. Produce a concise summary of the extracted content in clear English (≈100–150 words). Capture the main ideas, arguments, and conclusions without adding external information or speculation.
5. Return a JSON object that follows the `StructuredOutput` schema with exactly two fields: `url` (the provided URL) and `summary` (the generated concise summary).

ADDITIONAL GUIDELINES
• If the page cannot be fetched or has little textual content, explain the issue briefly in the `summary` field.
• Do not output anything except the valid JSON that matches the schema.
• Stay within 1000 total tokens for any intermediate reasoning.
"""  # noqa: E501

# ========== Tools definition ===========
TOOLS = [
    visit_webpage,
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


def main(url: str):
    """Given a webpage URL, the agent fetches the page, extracts its main text, and returns a concise summary."""
    input_prompt = f"Summarize the main text content from this webpage: {url}"
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
        "total_cost": cost_info.total_cost,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(trace_data, indent=2))

    return agent_trace.final_output


if __name__ == "__main__":
    Fire(main)
