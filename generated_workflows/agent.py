from any_agent import AgentConfig, AgentFramework, AnyAgent
from any_agent.tools import search_web, visit_webpage
from pydantic import BaseModel


class RestaurantInfo(BaseModel):
    name: str
    address: str
    rating: float | None = None
    review_count: int | None = None
    description: str | None = None
    url: str | None = None


if __name__ == "__main__":
    agent = AnyAgent.create(
        AgentFramework.OPENAI,
        AgentConfig(
            model_id="gpt-4o",  # Consider using latest OpenAI model for web tasks
            instructions=(
                "You are a research assistant helping users find top-rated restaurants. "
                "Use the available tools to search for the best sushi restaurant in Berlin. "
                "Return the result as a list of RestaurantInfo (name, address, rating, review_count, url, description). "
                "Be as concise and accurate as possible."
            ),
            tools=[search_web, visit_webpage],
            agent_args={"output_type": list[RestaurantInfo]},
        ),
    )
    agent_trace = agent.run(
        "Find the best sushi restaurant in Berlin. Return the result as a list of up to 3 RestaurantInfo."
    )
    print(agent_trace.final_output)
