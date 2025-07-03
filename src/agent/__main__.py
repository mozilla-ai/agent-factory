import dotenv
import fire
from any_agent import AgentConfig, AgentFramework, AnyAgent
from any_agent.serving import A2AServingConfig
from any_agent.tools import search_tavily, visit_webpage
from instructions import INSTRUCTIONS
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.trace import get_tracer_provider
from pydantic import BaseModel, Field
from utils import read_file, search_mcp_servers  # type: ignore[import-not-found]

dotenv.load_dotenv()


class AgentFactoryOutputs(BaseModel):
    agent_instructions: str = Field(..., description="The instructions passed to the generated agent.")
    tools: str = Field(..., description="The python code that defines the tools to be used by the generated agent.")
    imports: str = Field(..., description="The python code snippet used to import the required tools.")
    structured_outputs: str = Field(..., description="The Pydantic v2 models used to structure the agent's output.")
    cli_args: str = Field(..., description="The arguments to be provided to the agent from the command line.")
    agent_description: str = Field(..., description="The description of the agent and what it does.")
    prompt_template: str = Field(
        ..., description="A prompt template that, completed with cli_args, defines the agent's input prompt."
    )
    run_instructions: str = Field(..., description="The run instructions in Markdown format")
    dependencies: str = Field(..., description="The dependencies line by line in Markdown format")


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

    tp = get_tracer_provider()
    http_exporter = OTLPSpanExporter(endpoint="http://tempo:4318/v1/traces")
    tp.add_span_processor(SimpleSpanProcessor(http_exporter))

    agent = AnyAgent.create(
        framework,
        AgentConfig(
            model_id=model,
            instructions=INSTRUCTIONS,
            description="Agent for generating agentic workflows based on user prompts.",
            tools=[visit_webpage, search_tavily, search_mcp_servers, read_file],
            model_args={"tool_choice": "required"},  # Ensure tool choice is required
            output_type=AgentFactoryOutputs,
        ),
    )

    agent.serve(A2AServingConfig(host=host, port=port, log_level=log_level))


if __name__ == "__main__":
    fire.Fire(main)
