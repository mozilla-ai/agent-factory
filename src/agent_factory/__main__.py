import dotenv
from any_agent import AgentConfig, AgentFramework, AnyAgent
from any_agent.serving import A2AServingConfig
from any_agent.tools import search_tavily, visit_webpage

from agent_factory.instructions import INSTRUCTIONS
from agent_factory.tools import read_file, search_mcp_servers

dotenv.load_dotenv()


framework = AgentFramework.OPENAI
agent = AnyAgent.create(
    framework,
    AgentConfig(
        model_id="o3",
        instructions=INSTRUCTIONS,
        description="Agent for generating agentic workflows based on user prompts.",
        tools=[visit_webpage, search_tavily, search_mcp_servers, read_file],
        model_args={"tool_choice": "required"},  # Ensure tool choice is required
    ),
)

agent.serve(A2AServingConfig(port=5001, log_level="info"))
