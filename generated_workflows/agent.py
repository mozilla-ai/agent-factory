# agent.py
"""This script defines a single-agent workflow using Mozilla's any-agent library and the OpenAI framework
(model: gpt-4.1). The agent is designed to find the best sushi restaurant in Berlin by executing
a structured multi-step process with tool-augmented actions and outputs results as a structured JSON.
"""

import asyncio

from any_agent.agent import AnyAgent
from any_agent.config import AgentConfig
from pydantic import BaseModel, Field

# Step-by-step multi-step system instructions for the agent
INSTRUCTIONS = """
You are a restaurant recommendation expert specializing in Berlin. Your objective is to identify the best sushi restaurant in Berlin by following these steps:

Step 1: Clarify the Search Scope and Criteria
- Input: User asks for the best sushi restaurant in Berlin
- Action: Confirm that the request is about finding the single best sushi restaurant in Berlin based on available online reviews and rankings. Note any standard criteria (food quality, review scores, reputation).
- Output: State the criteria you will use and confirm the location (Berlin) and cuisine (sushi).

Step 2: Perform Online Search for Top Sushi Restaurants in Berlin
- Input: Clarified search scope and criteria
- Action: Use the 'search_web' tool to gather recent lists or review articles about the best sushi restaurants in Berlin (e.g., top 10/15 lists, review roundups from reputable publications or platforms).
- Output: Summarize the top candidates (at least 3) identified from the search, including their names and sources.

Step 3: Investigate the Leading Candidates in Depth
- Input: Names of top candidates from Step 2
- Action: For each leading candidate, use the 'visit_webpage' tool on their main website or leading online review page to gather details about:
    - Cuisine authenticity and restaurant highlights
    - Review excerpts/scores (from Google, TripAdvisor, Yelp, etc.)
    - Special features or distinguishing factors
- Output: For each candidate, provide a brief profile including these collected details.

Step 4: Select the Best Sushi Restaurant and Justify Choice
- Input: Profiles of candidates from Step 3
- Action: Using collected data, select the top restaurant (highest reviews, strongest reputation, most frequently recommended). Justify the choice based on the stated criteria.
- Output: Provide your final recommendation and the reasons for your choice.

Final Output: Provide the result in JSON with this format:
{
  "name": string, // Name of the selected restaurant
  "address": string, // If available from research
  "justification": string, // Brief explanation of why it is selected
  "other_top_candidates": [string] // Names of other highly ranked contenders
}
"""


# Pydantic v2 model for structured output
class SushiRecommendation(BaseModel):
    name: str = Field(..., description="Name of the selected restaurant")
    address: str = Field(..., description="Address of the selected restaurant (if found)")
    justification: str = Field(..., description="Explanation for why this restaurant was selected as the best")
    other_top_candidates: list[str] = Field(..., description="Other highly ranked sushi places considered")


# Configure the agent
agent_config = AgentConfig(
    framework="openai",
    model_id="gpt-4.1",
    instructions=INSTRUCTIONS,
    tools=["search_web", "visit_webpage"],
    output_type=SushiRecommendation,
)


async def main():
    agent = AnyAgent(agent_config)
    result = await agent.run("Find the best sushi restaurant in Berlin.")
    print("\nBest Sushi Restaurant Recommendation (Berlin):")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
