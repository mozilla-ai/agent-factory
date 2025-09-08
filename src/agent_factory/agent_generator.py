from pathlib import Path
from uuid import UUID

import fire
import httpx
from a2a.client import A2ACardResolver, A2AClient
from dotenv import find_dotenv, load_dotenv
from opentelemetry import trace
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.trace import TracerProvider

from agent_factory.config import TRACES_DIR
from agent_factory.schemas import Status
from agent_factory.utils import (
    create_a2a_http_client,
    create_agent_trace_from_dumped_spans,
    create_message_request,
    get_a2a_agent_card,
    get_storage_backend,
    logger,
    prepare_agent_artifacts,
    process_a2a_agent_final_response,
    process_streaming_response_message,
)

trace.set_tracer_provider(TracerProvider())
HTTPXClientInstrumentor().instrument()
tracer = trace.get_tracer(__name__)

PUBLIC_AGENT_CARD_PATH = "/.well-known/agent.json"
EXTENDED_AGENT_CARD_PATH = "/agent/authenticatedExtendedCard"


async def generate_target_agent(
    message: str,
    output_dir: Path | None = None,
    request_id: UUID | None = None,
    host: str = "localhost",
    port: int = 8080,
    timeout: int = 600,
) -> None:
    """Main entry point for the A2A client application.

    Args:
        message: The message to send to the agent.
        output_dir: Directory to save agent outputs. If None, a default is used.
        request_id: The request ID for the message.
        host: The host address for the agent server (default: "localhost").
        port: The port for the agent server (default: 8080).
        timeout: The timeout for the request in seconds (default: 600).
    """
    with tracer.start_as_current_span("generate_target_agent") as span:
        trace_id = trace.format_trace_id(span.get_span_context().trace_id)
        spans_dump_file_path = TRACES_DIR / f"0x{trace_id}.jsonl"
        # The same trace_id is used as the folder name when saving agent artifacts (on local/MinIO/S3),
        # if no output_dir is defined
        output_dir = output_dir if output_dir else trace_id
        storage_backend = get_storage_backend()
        response_json = None

        try:
            http_client, base_url = await create_a2a_http_client(host, port, timeout)
            async with http_client as client:
                resolver = A2ACardResolver(httpx_client=client, base_url=base_url)
                agent_card = await get_a2a_agent_card(resolver)

                client = A2AClient(httpx_client=client, agent_card=agent_card)
                logger.info("A2AClient initialized.")
                logger.info(f"Trace will be temporarily saved to {spans_dump_file_path}")

                request = create_message_request(message, request_id=request_id)

                responses = []
                async for response in client.send_message_streaming(request, http_kwargs={"timeout": timeout}):
                    processed_response = process_streaming_response_message(response)
                    if processed_response.message:
                        if processed_response.message_type == "info":
                            log_message = f"{processed_response.message} \n"
                            if processed_response.message_attributes:
                                log_message += f"{processed_response.message_attributes} \n"
                            logger.info(log_message)
                        else:
                            logger.error(processed_response.message)
                    responses.append(response)

                # Process response
                final_response = responses[-1]
                response = process_a2a_agent_final_response(final_response)
                response_json = response.model_dump_json()
                if response.status == Status.COMPLETED:
                    prepared_artifacts = prepare_agent_artifacts(response.model_dump())
                    logger.info(f"Saving agent artifacts to {output_dir} folder on {storage_backend.__str__()}")
                    storage_backend.save(prepared_artifacts, Path(output_dir))
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
        finally:
            # Upload trace regardless of success or failure for debugging purposes
            logger.info(f"Creating agent trace from {spans_dump_file_path}")
            agent_trace = create_agent_trace_from_dumped_spans([spans_dump_file_path], final_output=response_json)
            logger.info(f"Uploading agent trace to {output_dir} folder on {storage_backend}")
            storage_backend.upload_trace_file(agent_trace, Path(output_dir))


def main():
    load_dotenv(find_dotenv(".default.env", usecwd=True))
    load_dotenv(find_dotenv(".env", usecwd=True), override=True)
    fire.Fire(generate_target_agent)


if __name__ == "__main__":
    main()
