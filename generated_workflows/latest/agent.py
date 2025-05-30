"""Agent workflow to summarize text content from a given webpage URL using Mozilla's any-agent.
- Uses OpenAI (gpt-4.1) as the underlying LLM framework.
- Two-step workflow:
    1. Extract all human-readable text from the provided webpage URL (using extract_text_from_url)
    2. Summarize the extracted text to a concise paragraph (using summarize_text_with_llm)
- Structured output via Pydantic v2 model.
- Saves agent trace as JSON to generated_workflows/latest/agent_trace.json
"""

from any_agent import AgentConfig, AnyAgent
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from tools.extract_text_from_url import extract_text_from_url
from tools.summarize_text_with_llm import summarize_text_with_llm

load_dotenv()


# ====== Structured Output Model ======
class WebpageSummaryOutput(BaseModel):
    url: str = Field(..., description="The original URL from which text was extracted and summarized.")
    summary: str = Field(..., description="A concise summary of the extracted text content from the webpage.")


# ====== Agent Instructions ======
INSTRUCTIONS = (
    "You are a web content summarization agent. You must proceed step by step: "
    "1. First, use the `extract_text_from_url` tool to fetch and extract the human-readable text content from the given URL. "
    "2. Then, use the `summarize_text_with_llm` tool to summarize the extracted text to a concise paragraph. "
    "3. Output the result as a JSON object using the provided structured output model. "
    "If any step fails, provide an informative error message in the summary. "
    "Keep the summary directly relevant, accurate, and clear."
)

# ====== Create the Agent ======
agent = AnyAgent.create(
    "openai",
    AgentConfig(
        model_id="gpt-4.1",
        instructions=INSTRUCTIONS,
        tools=[extract_text_from_url, summarize_text_with_llm],
        agent_args={"output_type": WebpageSummaryOutput},
    ),
)

if __name__ == "__main__":
    import sys
    from pathlib import Path

    if len(sys.argv) < 2:
        print("Usage: python agent.py <webpage_url>")
        exit(1)
    url = sys.argv[1]

    # Run the agent
    agent_trace = agent.run(prompt=f"Summarize the content of this webpage: {url}")
    print("\n=== Summary ===\n", agent_trace.final_output)

    # Save the agent trace
    Path("/app/generated_workflows/latest").mkdir(parents=True, exist_ok=True)
    with open("/app/generated_workflows/latest/agent_trace.json", "w", encoding="utf-8") as f:
        f.write(agent_trace.model_dump_json(indent=2))
