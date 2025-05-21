import os

from any_agent import AgentConfig, AnyAgent
from any_agent.config import MCPStdio
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from tools.generate_podcast_script_with_llm import generate_podcast_script_with_llm
from tools.summarize_text_with_llm import summarize_text_with_llm
from tools.translate_text_with_llm import translate_text_with_llm

load_dotenv()


# Pydantic model for structured output
class PodcastScriptOutput(BaseModel):
    topic: str = Field(..., description="Podcast topic that was researched and scripted.")
    summary: str = Field(..., description="Concise summary of the latest news used for script generation, English.")
    podcast_script_spanish: str = Field(..., description="Podcast script in Spanish.")


INSTRUCTIONS = """
Your goal is to generate an engaging podcast script in Spanish about a user-specified topic, incorporating the latest news. You should break down the work as follows:

Step 1: Perform a Brave web search on the topic to find current news or major recent developments. Focus on retrieving reputable, recent, and relevant articles (if available).
Step 2: Concisely summarize the key news/developments found (in English, a concise paragraph, eliminate all redundancy and focus on newsworthy content).
Step 3: Turn the summary into an engaging two-host podcast script in English, designed to clearly explain the recent news or developments to an audience.
Step 4: Translate the full script from English to Spanish.
Step 5: Output the following in structured JSON: (a) the topic, (b) the summary (English), and (c) the final Spanish podcast script.
"""

agent = AnyAgent.create(
    "openai",
    AgentConfig(
        model_id="gpt-4.1",
        instructions=INSTRUCTIONS,
        tools=[
            # Use the Brave web search MCP for current news
            MCPStdio(
                command="docker",
                args=["run", "-i", "--rm", "-e", "BRAVE_API_KEY", "mcp/brave-search"],
                env={"BRAVE_API_KEY": os.getenv("BRAVE_API_KEY")},
                tools=["brave_web_search"],
            ),
            summarize_text_with_llm,
            generate_podcast_script_with_llm,
            translate_text_with_llm,
        ],
        agent_args={"output_type": PodcastScriptOutput},
    ),
)

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python agent.py '<topic>'")
        exit(1)
    topic = sys.argv[1]
    result = agent.run(prompt=f"Generate a Spanish podcast script about: {topic}")
    print(result)
