import dotenv
import fire
from any_agent import AgentConfig, AgentFramework, AnyAgent
from any_agent.serving import A2AServingConfig
from any_agent.tools import search_tavily, visit_webpage
from factory_tools import read_file, search_mcp_servers
from instructions import load_system_instructions
from schemas import AgentFactoryOutputs

dotenv.load_dotenv()


async def main(
    framework: str = "openai",
    model: str = "o3",
    host: str = "localhost",
    port: int = 8080,
    log_level: str = "info",
):
    """Main entry point for the agent application.

    Args:
        framework (str): The agent framework to use (default: "openai").
        model (str): The model ID to use (default: "o3").
        host (str): The host address for the agent server (default: "localhost").
        port (int): The port for the agent server (default: 8080).
        log_level (str): The logging level (default: "info").
    """
    try:
        AgentFramework[framework.upper()]
    except KeyError as err:
        raise ValueError(
            f"Invalid framework '{framework}'. Allowed values are: {[f.name.lower() for f in AgentFramework]}"
        ) from err

    agent = await AnyAgent.create_async(
        framework,
        AgentConfig(
            model_id=model,
            instructions=load_system_instructions(for_cli_agent=False),
            description="Agent for generating agentic workflows based on user prompts.",
            tools=[visit_webpage, search_tavily, search_mcp_servers, read_file],
            model_args={"tool_choice": "required"},  # Ensure tool choice is required
            output_type=AgentFactoryOutputs,
        ),
    )

    server_handle = await agent.serve_async(A2AServingConfig(host=host, port=port, log_level=log_level))

    try:
        # Keep the server running
        await server_handle.task
    except KeyboardInterrupt:
        await server_handle.shutdown()


if __name__ == "__main__":
    fire.Fire(main)
