
# agent.py

# good to have

# ALWAYS used
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
    url: str = Field(..., description="The URL that was summarised.")
    summary: str = Field(..., description="A concise summary of the page content (≤200 words).")

# ========== System (Multi-step) Instructions ===========
INSTRUCTIONS='''
You are an assistant that produces a concise summary of any public web page.
Work step-by-step and never skip a step.

Step-1 – Fetch:
• Receive exactly one URL from the user.
• Call the tool `extract_text_from_url` with that URL to obtain the plain text of the page (body content only, exclude navigation, ads, boiler-plate).

Step-2 – Validate:
• If the extracted text is fewer than 50 words, reply that there is not enough content to summarise and stop.
• Otherwise proceed.

Step-3 – Summarise:
• Call the tool `summarize_text_with_llm` on the extracted text.
• Ask for a short, clear overview no longer than 200 words written in the third person.

Step-4 – Respond:
• Return a JSON object that follows the `StructuredOutput` schema strictly.
• Fields:
    – url: echo the input URL.
    – summary: the generated summary.
• Do NOT include any additional keys.
• The final answer MUST be valid JSON.
'''

# ========== Tools definition ===========
# ========== Tools definition ===========
TOOLS = [
    extract_text_from_url,       # fetch & clean webpage text
    summarize_text_with_llm,    # create the summary via LLM
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
    """Given a web URL, retrieve the page’s main text and return a concise summary as JSON."""
    input_prompt = f"Summarise the content of this webpage: {url}"
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

