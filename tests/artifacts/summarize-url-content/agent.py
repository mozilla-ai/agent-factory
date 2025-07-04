
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
# ========= Structured output definition ==========
class StructuredOutput(BaseModel):
    url: str = Field(..., description="The original webpage URL provided by the user.")
    extracted_text: str = Field(..., description="The raw human-readable text extracted from the webpage (possibly truncated if extremely long).")
    summary: str = Field(..., description="A concise paragraph summarising the webpage content.")

# ========== System (Multi-step) Instructions ===========
INSTRUCTIONS='''
You are a helpful assistant that produces a concise summary of a given webpage by executing the following minimal, strictly ordered steps:
1. Input Validation – Receive a single webpage URL from the user. If the URL is clearly malformed (e.g., missing scheme or domain), respond with a clear error inside the structured output and stop.
2. Content Extraction – Invoke the `extract_text_from_url` tool with the provided URL to obtain the raw human-readable text.
   • If the tool returns an error message beginning with "Error", place that message in the `extracted_text` field, leave the `summary` field empty, and stop.
3. Summarisation – Call the `summarize_text_with_llm` tool, asking for “a concise paragraph” length. Provide it the full extracted text.
4. Assemble Output – Return a JSON object matching the `StructuredOutput` schema with:
   • url – the original URL
   • extracted_text – up to the first 1 000 words of the extracted text (trim if longer)
   • summary – the paragraph-length summary generated in step 3
Keep all content factual; never fabricate webpage text. Do not output anything other than the final JSON object.
'''

# ========== Tools definition ===========
# ========= Tools definition =========
TOOLS = [
    extract_text_from_url,   # fetch and extract visible text from URL
    summarize_text_with_llm, # create a concise summary
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
    """Fetches the main text from a supplied webpage URL and returns a concise summary in structured JSON form."""
    input_prompt = f"Summarise the content of this webpage: {url}"
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

