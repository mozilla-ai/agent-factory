from any_agent import AgentConfig, AnyAgent
from any_agent.tools import search_web, visit_webpage
from pydantic import BaseModel, Field


class RestaurantInfo(BaseModel):
    name: str = Field(..., description="Name of the sushi restaurant")
    rating: float = Field(..., description="Restaurant's average rating (out of 5)")
    address: str = Field(..., description="Physical address of the restaurant")
    description: str = Field(..., description="Short summary or unique selling points")
    url: str = Field(..., description="Website or reference URL, if available")


class RestaurantResults(BaseModel):
    best_restaurant: RestaurantInfo
    alternatives: list[RestaurantInfo] = Field(
        default_factory=list, description="Other highly-rated sushi restaurants in Berlin, if any."
    )


def main():
    instructions = (
        "You are a world-class foodie assistant. Your job is to use the available tools "
        "to find the best sushi restaurant in Berlin. "
        "Report the top choice, with details, and up to 2 good alternatives. "
        "Focus on recent, reliable information. Make sure your final answer is structured using the RestaurantResults pydantic model."
    )
    agent = AnyAgent.create(
        "openai",
        AgentConfig(
            model_id="gpt-4o",  # Change to "gpt-4.1-nano" or another if needed
            instructions=instructions,
            tools=[search_web, visit_webpage],
            agent_args={"output_type": RestaurantResults},
        ),
    )
    agent_trace = agent.run("Find me the best sushi restaurant in Berlin.")
    # Structured output in agent_trace.final_output
    print(agent_trace.final_output)
    agent.exit()


if __name__ == "__main__":
    main()
