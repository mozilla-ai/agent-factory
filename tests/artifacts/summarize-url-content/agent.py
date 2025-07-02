
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
    url: str = Field(..., description="The webpage URL provided by the user.")
    extracted_text: str = Field(..., description="The plaintext extracted from the webpage (may be truncated).")
    summary: str = Field(..., description="A concise summary of the extracted text.")


# ========== System (Multi-step) Instructions ===========
INSTRUCTIONS='''
You are an assistant that follows this 3-step workflow to provide a concise summary of any public webpage supplied by the user.
Step 1 – Fetch & Extract
• Receive a single web URL from the user.
• Use the extract_text_from_url tool to download the page and extract all human-readable text.
• If the tool returns an error string (it starts with “Error”), immediately halt, returning a StructuredOutput object whose summary field contains a short apology plus the error.
Step 2 – Summarise
• Pass the extracted text to the summarize_text_with_llm tool.
• Ask for “a concise paragraph” unless the extracted text is longer than 8 000 characters, in which case ask for “five key bullet points”.
• Store the resulting summary.
Step 3 – Respond
• Return a StructuredOutput JSON object with these fields:
    url – the original user URL
    extracted_text – the raw text returned in Step 1 (trimmed to the first 4 000 characters to avoid extremely long outputs; add “[…]” if truncated)
    summary – the summary produced in Step 2.
General rules:
• Never invent content; base the summary strictly on the extracted text.
• Keep the total response under 1 000 tokens.
• Do not reveal internal reasoning or tool call details to the user.

'''

# ========== Tools definition ===========
# ========== Tools definition =========
from tools.extract_text_from_url import extract_text_from_url
from tools.summarize_text_with_llm import summarize_text_with_llm

TOOLS = [
    extract_text_from_url,  # fetch & extract webpage text
    summarize_text_with_llm # generate the summary
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
    """Given a web URL, fetches the page, extracts its main text content, and returns a concise summary inside a StructuredOutput object."""
    input_prompt = f"Summarise the content of the following webpage URL: {url}"
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

