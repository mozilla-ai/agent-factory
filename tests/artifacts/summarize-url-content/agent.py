# agent.py

import os
from typing import Optional

from dotenv import load_dotenv
from any_agent import AgentConfig, AnyAgent, AgentRunError
from pydantic import BaseModel, Field
from fire import Fire

# === Local tools ===
from tools.extract_text_from_url import extract_text_from_url
from tools.summarize_text_with_llm import summarize_text_with_llm

load_dotenv()

# ========== Structured output definition ==========
class StructuredOutput(BaseModel):
    """Final response returned by the agent."""

    url: str = Field(..., description="The input URL that was processed.")
    extracted_text: str = Field(
        ..., description="The raw text extracted from the webpage (may be truncated)."
    )
    summary: str = Field(..., description="A concise summary of the page content.")


# ========== System (Multi-step) Instructions ==========
INSTRUCTIONS = """
You are a multi-step assistant that produces a structured JSON summary for any public webpage.

Workflow:
1. Receive an input URL and the desired summary length description from the user.
2. Use the `extract_text_from_url` tool to fetch and clean the full textual content of the page.
   • If the tool returns an error message (it starts with the word "Error"), immediately produce the
     final JSON output where `summary` contains that error message and `extracted_text` is the
     original error string.
3. Truncate the extracted text to at most ~1 500 characters so the JSON stays compact. Preserve
   whole sentences where possible.
4. Use `summarize_text_with_llm` to create a summary of the extracted text. Pass the user-supplied
   `summary_length` argument so the style/length matches the request.
5. Return a JSON object following the `StructuredOutput` schema with the keys:
   • url – the original URL
   • extracted_text – the (possibly truncated) extracted text
   • summary – the generated summary or an error explanation
"""

# ========== Tools definition ==========
TOOLS = [
    extract_text_from_url,  # Pull and clean raw page text
    summarize_text_with_llm,  # Turn raw text into a short summary
]

# ========== Agent ========== 
agent = AnyAgent.create(
    "openai",
    AgentConfig(
        model_id="o3",
        instructions=INSTRUCTIONS,
        tools=TOOLS,
        output_type=StructuredOutput,
        # Require the agent to call tools to build the final answer
        model_args={"tool_choice": "required"},
    ),
)


# ========== CLI wrapper ==========
PROMPT_TEMPLATE = (
    "Summarize the webpage at the given URL using the requested summary style.\n"
    "URL: {url}\n"
    "Desired summary style: {summary_length}"
)


def run_agent(url: str, summary_length: str = "a concise paragraph") -> StructuredOutput:  # type: ignore[type-var]
    """Extract text from a webpage and return a structured summary.

    Args:
        url: The webpage URL to summarise.
        summary_length: A natural-language description of the desired summary length or style,
                        e.g. "a concise paragraph", "three bullet points", etc.
    Returns:
        A StructuredOutput Pydantic object with url, extracted_text, and summary fields.
    """

    input_prompt = PROMPT_TEMPLATE.format(url=url, summary_length=summary_length)

    try:
        agent_trace = agent.run(prompt=input_prompt, max_turns=20)
    except AgentRunError as e:
        # Even on failure we capture the trace for evaluation
        agent_trace = e.trace
        print(f"Agent execution failed: {e}")
        print("Retrieved partial agent trace...")

    # Persist trace for later evaluation
    with open("generated_workflows/latest/agent_eval_trace.json", "w", encoding="utf-8") as f:
        f.write(agent_trace.model_dump_json(indent=2))

    return agent_trace.final_output  # type: ignore[return-value]


if __name__ == "__main__":
    Fire(run_agent)