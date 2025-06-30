
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
# ========== Structured output definition ==========
class StructuredOutput(BaseModel):
    url: str = Field(..., description="The webpage URL that was summarized.")
    summary: str = Field(..., description="A concise summary of the webpage content (≤180 words).")

# ========== System (Multi-step) Instructions ===========
INSTRUCTIONS='''
You are an expert summarization agent.  Follow this exact 3-step workflow for EVERY request:\n\nStep 1 – Extract text\n  • Use the `extract_text_from_url` tool with the provided `url` to fetch and clean all human-readable text from the webpage.  \n  • If the tool returns an error string (it starts with "Error"), STOP and reply with a JSON object containing the key `summary` whose value clearly states the failure reason.\n\nStep 2 – Summarize\n  • Pass the extracted text to `summarize_text_with_llm`.  \n  • Ask for “a concise paragraph” as the `summary_length` argument.  \n  • Ensure the summary is factual, free of hallucinations, and no longer than 180 words.\n\nStep 3 – Respond\n  • Return a JSON object that matches the `StructuredOutput` schema exactly.  \n  • The `summary` field must hold ONLY the final summary (no extra keys, explanation, or step logs).  \n\nGeneral rules:\n  • Work step-by-step but DO NOT reveal chain-of-thought.\n  • Use ONLY the tools provided in the TOOLS list.  \n  • Output MUST be valid JSON conforming to the `StructuredOutput` model.
'''

# ========== Tools definition ===========
# ========== Tools definition ===========
TOOLS = [
    extract_text_from_url,   # Fetch & clean webpage text
    summarize_text_with_llm  # Produce concise LLM summary
]

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

def run_agent(url: str):
    """Given a webpage URL, the agent extracts the page’s main text and returns a concise summary as structured JSON."""
    input_prompt = f"Please summarize the content of the following webpage URL: {url}"
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
    Fire(run_agent)

