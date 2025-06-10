# agent.py
"""
Agent: Webpage Content Summarizer (Single-Agent, Multi-Step)
-----------------------------------------------------------
Summarizes text content from a given webpage URL using any-agent, OpenAI's GPT-4.1 model, and structured output via Pydantic.
"""

from any_agent import AnyAgent, AgentConfig
from any_agent.tools import visit_webpage
from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# === Pydantic model for structured output ===
class WebpageSummaryOutput(BaseModel):
    url: str = Field(..., description="The original webpage URL that was summarized.")
    summary: str = Field(..., description="A concise summary of the main textual content from the webpage.")

# === Detailed Step-by-Step Agent Instructions ===
INSTRUCTIONS = """
You are an expert assistant whose task is to summarize text content from a webpage given its URL. Follow this precise workflow:

Step 1: Receive the input URL from the user prompt.
Step 2: Use the provided 'visit_webpage' tool to retrieve the text and main content from the given URL. Only use the content returned by the tool; do not hallucinate or use external information.
Step 3: Read the webpage content carefully. Identify and focus on the main body text, skipping headers, footers, navigation, ads, and unrelated material.
Step 4: Write a clear, concise summary (4-6 sentences) capturing the essential points and main arguments or information from the body text. Do not include a list of sections, metadata, or raw sentences; your summary should be human-readable and coherent.
Step 5: Output your results as JSON with two fields:
- 'url': the original webpage URL
- 'summary': your generated summary
Your output MUST match the schema given. Never return information not present in the visited webpage.
"""

# === Agent instantiation ===
agent = AnyAgent.create(
    "openai",
    AgentConfig(
        model_id="gpt-4.1",
        instructions=INSTRUCTIONS,
        tools=[
            visit_webpage,
        ],
        agent_args={
            "output_type": WebpageSummaryOutput,
        },
    ),
)

# === Sample agent run ===
if __name__ == "__main__":
    # User supplies a prompt in the form of a URL (edit as needed or integrate your own input method)
    user_input_url = "https://mozilla-ai.github.io/any-agent/agents/"  # Example URL, change as necessary
    prompt = f"Summarize the main textual content from this webpage: {user_input_url}"

    agent_trace = agent.run(prompt=prompt)

    # Save agent trace as JSON
    with open("generated_workflows/latest/agent_eval_trace.json", "w", encoding="utf-8") as f:
        f.write(agent_trace.model_dump_json(indent=2))