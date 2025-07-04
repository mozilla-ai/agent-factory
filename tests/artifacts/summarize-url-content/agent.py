
# agent.py

# good to have

# ALWAYS used
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
    url: str = Field(..., description="The URL that was summarised.")
    summary: str = Field(..., description="A concise paragraph summarising the main content of the webpage.")

# ========== System (Multi-step) Instructions ===========
INSTRUCTIONS='''
You are a helpful assistant that produces a concise summary of any public webpage provided by the user.  Follow this 3-step workflow strictly and use the designated tools at each step.

STEP-1 – Extract text
• Receive the input URL from the user prompt.
• Call the tool `extract_text_from_url` with that URL.
• If the tool returns a string that starts with "Error", immediately finish and return a JSON object where the field `summary` contains the error message.

STEP-2 – Summarise
• Take the extracted plain-text returned from STEP-1.
• Call the tool `summarize_text_with_llm` with the text and ask for “a concise paragraph” as the summary length.
• The summary must be factual, faithful to the source, and 2-6 sentences long (≈100-150 words).  Do NOT add opinions or external information.

STEP-3 – Final output
• Return a JSON object that matches the `StructuredOutput` schema:
  – url: the original URL supplied by the user.
  – summary: the paragraph produced in STEP-2.

Always follow this exact order of operations and use the tools explicitly; do not attempt to fetch or summarise the page without them.
'''

# ========== Tools definition ===========
from any_agent.tools import visit_webpage  # (import kept only to satisfy any-agent’s internal checks – NOT used)

TOOLS = [
    extract_text_from_url,        # fetch & extract readable text from the web page
    summarize_text_with_llm,      # create a concise summary of the extracted text
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
    """Given a webpage URL, the agent extracts its readable text and returns a concise summary in JSON format."""
    input_prompt = f"Summarise the content of the following webpage: {url}"
    try:
        agent_trace = agent.run(prompt=input_prompt, max_turns=20)
    except AgentRunError as e:
        agent_trace = e.trace
        print(f"Agent execution failed: {str(e)}")
        print("Retrieved partial agent trace...")

    script_dir = Path(__file__).resolve().parent
    output_path = script_dir / "agent_eval_trace.json"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(agent_trace.model_dump_json(indent=2))

    return agent_trace.final_output

if __name__ == "__main__":
    Fire(main)

