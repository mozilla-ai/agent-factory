from any_agent import AgentConfig, AnyAgent
from pydantic import BaseModel, Field
from tools.extract_text_from_url import extract_text_from_url
from tools.summarize_text_with_llm import summarize_text_with_llm


# Structured output model for the agent's response
class WebpageSummaryOutput(BaseModel):
    url: str = Field(..., description="Webpage URL that was summarized.")
    summary: str = Field(..., description="Concise summary of the webpage content.")
    extracted_text: str = Field(..., description="Full extracted text from the webpage.")


# Multi-step detailed instructions for the agent
INSTRUCTIONS = """
You are a two-step assistant. You will be given a webpage URL. Your task is to summarize its content accurately as follows:

Step 1: Use the extract_text_from_url tool to extract all readable, human-intelligible text from the provided URL. If the tool returns an error or empty content, report the extraction error and do not proceed with summarization.

Step 2: Take the extracted text and summarize it into a concise paragraph suitable for a general audience. Use the summarize_text_with_llm tool with summary_length set to 'a concise paragraph'. The summary should capture the main point(s) and theme of the webpage.

Return both the original URL, the summary, and the full extracted text in the structured output.
"""

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

    if len(sys.argv) < 2:
        print("Usage: python agent.py <webpage_url>")
        exit(1)
    url = sys.argv[1]
    user_prompt = f"Summarize the content of this webpage: {url}"
    result = agent.run(prompt=user_prompt)
    print("=== SUMMARY OUTPUT ===")
    print(result)
