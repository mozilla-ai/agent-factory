from pathlib import Path

import fire
import httpx
from a2a.client import A2ACardResolver, A2AClient
from opentelemetry import trace
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.trace import TracerProvider

from agent_factory.schemas import Status
from agent_factory.utils import (
    create_a2a_http_client,
    create_message_request,
    get_a2a_agent_card,
    process_a2a_agent_response,
    save_agent_outputs,
    setup_output_directory,
)
from agent_factory.utils.logging import logger

trace.set_tracer_provider(TracerProvider())
HTTPXClientInstrumentor().instrument()
tracer = trace.get_tracer(__name__)

PUBLIC_AGENT_CARD_PATH = "/.well-known/agent.json"
EXTENDED_AGENT_CARD_PATH = "/agent/authenticatedExtendedCard"


async def generate_target_agent(
    message: str,
    output_dir: Path | None = None,
    host: str = "localhost",
    port: int = 8080,
    timeout: int = 600,
) -> None:
    """Main entry point for the A2A client application.

    Args:
        message: The message to send to the agent.
        output_dir: Directory to save agent outputs. If None, a default is used.
        host: The host address for the agent server (default: "localhost").
        port: The port for the agent server (default: 8080).
        timeout: The timeout for the request in seconds (default: 600).
    """
    with tracer.start_as_current_span("generate_target_agent") as span:
        trace_file = f"0x{trace.format_trace_id(span.get_span_context().trace_id)}.json"

        try:
            http_client, base_url = await create_a2a_http_client(host, port, timeout)
            async with http_client as client:
                resolver = A2ACardResolver(httpx_client=client, base_url=base_url)
                agent_card = await get_a2a_agent_card(resolver)

                client = A2AClient(httpx_client=client, agent_card=agent_card)
                logger.info("A2AClient initialized.")
                logger.info(f"Trace will be saved to {trace_file}")

                request = create_message_request(message)
                response = await client.send_message(request, http_kwargs={"timeout": timeout})
                response = process_a2a_agent_response(response)
                if response.status == Status.COMPLETED:
                    output_dir = setup_output_directory(output_dir)
                    save_agent_outputs(response.model_dump(), output_dir)
                elif response.status == Status.INPUT_REQUIRED:
                    logger.info(
                        f"Please try again and be more specific with your request. Agent's response: {response.message}"
                    )
                else:
                    logger.error(f"Agent encountered an error: {response.message}")
                    raise Exception(f"Agent encountered an error: {response.message}")
        except httpx.ConnectError as e:
            logger.error(f"Failed to connect to the agent server at {host}:{port}. Error: {e}")
            raise RuntimeError(f"Connection to agent server failed: {e}") from e
        except httpx.TimeoutException as e:
            logger.error(f"Request to the agent server timed out after {timeout} seconds. Error: {e}")
            raise RuntimeError(f"Request to agent server timed out: {e}") from e
        except Exception as e:
            logger.error(f"An unexpected error occurred during agent generation: {e}")
            raise

    """
    This is how you can retrieve the trace after the generation is completed/interrupted
    full_trace = json.loads((Path("traces") / trace_file).read_text())
    """


def main():
    fire.Fire(generate_target_agent)


if __name__ == "__main__":
    fire.Fire(main)
