
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
# ADD BELOW HERE: tools made available by any-agent or agent-factory
from tools.extract_text_from_url import extract_text_from_url
from tools.summarize_text_with_llm import summarize_text_with_llm

load_dotenv()

# ========== Structured output definition ==========
# ========== Structured output definition ==========
class StructuredOutput(BaseModel):
    url: str = Field(..., description="The webpage URL provided by the user.")
    extracted_text: str = Field(..., description="The main textual content extracted from the webpage.")
    summary: str = Field(..., description="A concise summary (≤200 words) of the webpage content.")

# ========== System (Multi-step) Instructions ===========
INSTRUCTIONS='''
You are an assistant that, given a webpage URL, returns a concise summary of its main content. Work through these steps:
1. Use the `extract_text_from_url` tool to visit the page and extract the primary textual content. Strip away navigation menus, ads, footers, scripts, and any non-informative elements. Keep only the meaningful body text.
2. Pass the extracted text to the `summarize_text_with_llm` tool. Produce a clear, accurate, and self-contained summary no longer than 200 words. The summary must capture the key points and overall message of the page without adding external information.
3. Reply **only** with a JSON object that matches the `StructuredOutput` schema. Populate:
   • `url` – the original URL.
   • `extracted_text` – the cleaned raw text you retrieved.
   • `summary` – the 200-word (max) summary you generated.
Follow the steps strictly, do not skip any, and do not include any additional fields in the final response.
'''

# ========== Tools definition ===========
# ========= Tools definition =========
TOOLS = [
    extract_text_from_url,      # fetch & clean page text
    summarize_text_with_llm,    # produce concise summary
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
    """Extracts text from a webpage and returns a concise summary of its content."""
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

