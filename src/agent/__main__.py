import dotenv
import fire
from any_agent import AgentConfig, AgentFramework, AnyAgent
from any_agent.serving import A2AServingConfig
from any_agent.tools import search_tavily, visit_webpage
from factory_tools import read_file, search_mcp_servers
from instructions import load_system_instructions
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.trace import get_tracer_provider
from redis_exporter import RedisSpanExporter
from schemas import AgentFactoryOutputs

dotenv.load_dotenv()


def main(
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

    trace_provider = get_tracer_provider()
    redis_exporter = RedisSpanExporter()
    trace_provider.add_span_processor(SimpleSpanProcessor(redis_exporter))  # type: ignore

    agent = AnyAgent.create(
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

    agent.serve(A2AServingConfig(host=host, port=port, log_level=log_level))


if __name__ == "__main__":
    fire.Fire(main)
