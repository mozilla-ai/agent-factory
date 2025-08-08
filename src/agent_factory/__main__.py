import dotenv
import fire
from opentelemetry import trace
from opentelemetry.instrumentation.starlette import StarletteInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    SimpleSpanProcessor,
)

from agent_factory.config import TRACES_DIR
from agent_factory.factory_tools import read_file, search_mcp_servers
from agent_factory.instructions import load_system_instructions
from agent_factory.schemas import AgentFactoryOutputs
from agent_factory.utils import logger
from agent_factory.utils.json_exporter import JsonFileSpanExporter

dotenv.load_dotenv()


trace.set_tracer_provider(TracerProvider())
span_processor = SimpleSpanProcessor(JsonFileSpanExporter(TRACES_DIR))
trace.get_tracer_provider().add_span_processor(span_processor)

StarletteInstrumentor().instrument()


async def main(
    framework: str = "openai",
    chat: bool = True,
    model: str = "o3",
    max_turns: int = 40,
    host: str = "localhost",
    port: int = 8080,
    log_level: str = "info",
):
    """Main entry point for the agent application.

    Args:
        framework (str): The agent framework to use
        chat (bool): Whether to enable multi-turn conversations
        model (str): The model ID to use
        max_turns (int): The maximum number of turns that the agent can take
        host (str): The host address for the agent server
        port (int): The port for the agent server
        log_level (str): The logging level
    """
    from any_agent import AgentConfig, AgentFramework, AnyAgent
    from any_agent.callbacks import get_default_callbacks
    from any_agent.serving import A2AServingConfig
    from any_agent.tools import search_tavily, visit_webpage
    from agent_factory.callbacks import LimitAgentTurns

    try:
        AgentFramework[framework.upper()]
    except KeyError as err:
        raise ValueError(
            f"Invalid framework '{framework}'. Allowed values are: {[f.name.lower() for f in AgentFramework]}"
        ) from err

    logger.info(f"Starting the server in {'chat' if chat else 'non-chat'} mode.")

    agent = await AnyAgent.create_async(
        framework,
        AgentConfig(
            model_id=model,
            instructions=load_system_instructions(chat=chat),
            description="Agent for generating agentic workflows based on user prompts.",
            tools=[visit_webpage, search_tavily, search_mcp_servers, read_file],
            callbacks=[*get_default_callbacks(), LimitAgentTurns(max_turns=max_turns)],
            model_args={"tool_choice": "auto"},
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
