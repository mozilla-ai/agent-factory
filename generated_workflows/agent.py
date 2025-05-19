"""agent.py
=======================================

A single agent implementation using Mozilla's any-agent library to find the best sushi restaurant in Berlin, using OpenAI's GPT-4.1 and web browsing tools.

- Framework: OpenAI (gpt-4.1)
- Tools: search_web, visit_webpage
- Output: Structured JSON using Pydantic v2
- Modular, well-documented code

Instructions for running: see INSTRUCTIONS.md
"""

from any_agent import AgentConfig, AnyAgent
from any_agent.tools import search_web, visit_webpage
from pydantic import BaseModel, Field

# Multi-step, clear instructions for the agent
INSTRUCTIONS = """
Your task is to identify the best sushi restaurant in Berlin for a user.
Please follow these steps in order:

1. Use the web search tool to find recent rankings, articles, or reviews about sushi restaurants in Berlin. Look for lists, awards, or any reputed website results.
2. Review the top few search results by visiting the webpages that provide actual rankings, details, or comprehensive reviews. Collect information on top-rated sushi restaurants in Berlin, focusing on consistent mentions, user ratings, and expert opinions.
3. Based on your review, select one restaurant that stands out as the best according to the gathered evidence. Summarize the reasoning for your selection, citing the sources you used (with links where possible).
4. Output the information in structured JSON following the given schema.

Be comprehensive but concise. Only cite publicly accessible sources. Prioritize consensus among reputable listings.
"""


# Structured output using Pydantic model (v2 syntax)
class RestaurantInfo(BaseModel):
    name: str = Field(..., description="Restaurant name")
    address: str | None = Field(None, description="Address of the restaurant, if available")
    website: str | None = Field(None, description="Official website URL, if available")
    rating: str | None = Field(None, description="Rating if available (text or numeric)")
    description: str | None = Field(None, description="Short description or what makes it the best")
    sources: list[str] = Field(..., description="List of URLs (strings) of sources used to justify the selection")


# Configure the single agent
agent = AnyAgent.create(
    "openai",
    AgentConfig(
        model_id="gpt-4.1",
        instructions=INSTRUCTIONS,
        tools=[search_web, visit_webpage],
        agent_args={
            # This will cause the final output to be validated and formatted as RestaurantInfo
            "output_type": RestaurantInfo
        },
    ),
)


def main():
    # Run the agent on the sushi restaurant task
    trace = agent.run("What is the best sushi restaurant in Berlin? Please provide justification and sources.")
    print("\n==== STRUCTURED RESULT ====")
    print(trace.final_output)


if __name__ == "__main__":
    main()
