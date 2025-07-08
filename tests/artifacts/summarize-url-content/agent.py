
# agent.py

# good to have

# ALWAYS used
import json
from pathlib import Path
from dotenv import load_dotenv
from any_agent import AgentConfig, AnyAgent, AgentRunError
from pydantic import BaseModel, Field
from fire import Fire

# ADD BELOW HERE: tools made available by any-agent or agent-factory
from tools.extract_text_from_url import extract_text_from_url
from tools.summarize_text_with_llm import summarize_text_with_llm

load_dotenv()

# ========== Structured output definition ==========
class StructuredOutput(BaseModel):
    url: str = Field(..., description="The webpage URL that was summarized.")
    summary: str = Field(..., description="A concise paragraph summarizing the page content.")

# ========== System (Multi-step) Instructions ===========
INSTRUCTIONS='''
You are an assistant that produces concise summaries of webpages by following this structured, two-step workflow:
1. Extract Main Text
   • Use the `extract_text_from_url` tool to fetch the webpage located at the user-supplied URL and return its primary textual content (body, articles, posts). Strip boilerplate such as navigation, ads, and footer text. Work on English and non-English pages alike.
   • If no meaningful text is found, respond with an error message in the summary field indicating the page is empty or not accessible.

2. Summarize Content
   • Pass the extracted text to `summarize_text_with_llm` requesting a concise, well-structured paragraph (≈150 words maximum). Capture the essence, key points, and tone without adding new information.
   • Ensure the summary is self-contained—readers should grasp the page topic without visiting the link.

Output Requirements
• Always return a JSON object matching the `StructuredOutput` schema.
• Do not include any additional keys. Do not reveal internal tool calls or reasoning.
• Keep the summary free of sensitive or private data.
• If an error occurs at any step, return the URL and a brief error explanation in the `summary` field.

'''

# ========== Tools definition ===========
TOOLS = [
    extract_text_from_url,          # fetch & extract webpage text
    summarize_text_with_llm,        # create concise summary with an LLM
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

def main(url: str):
    """Given a webpage URL, this agent extracts the main textual content of the page and delivers a concise summary."""
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

