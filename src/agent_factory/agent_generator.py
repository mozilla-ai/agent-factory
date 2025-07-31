from pathlib import Path

import fire
from a2a.client import A2ACardResolver, A2AClient
from dotenv import find_dotenv, load_dotenv

from agent_factory.schemas import Status
from agent_factory.utils import (
    create_a2a_http_client,
    create_message_request,
    get_a2a_agent_card,
    get_storage_backend,
    logger,
    prepare_agent_artifacts,
    process_a2a_agent_response,
)

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
    http_client, base_url = await create_a2a_http_client(host, port, timeout)
    async with http_client as client:
        resolver = A2ACardResolver(httpx_client=client, base_url=base_url)
        agent_card = await get_a2a_agent_card(resolver)

        # Initialize client and send message
        client = A2AClient(httpx_client=client, agent_card=agent_card)
        logger.info("A2AClient initialized.")

        request = create_message_request(message)
        response = await client.send_message(request, http_kwargs={"timeout": timeout})

        # Process response
        response = process_a2a_agent_response(response)
        if response.status == Status.COMPLETED:
            prepared_artifacts = prepare_agent_artifacts(response.model_dump())
            storage_backend = get_storage_backend()
            storage_backend.save(prepared_artifacts, output_dir)
        elif response.status == Status.INPUT_REQUIRED:
            logger.info(
                f"Please try again and be more specific with your request. Agent's response: {response.message}"
            )
        else:
            logger.error(f"Agent encountered an error: {response.message}")


def main():
    load_dotenv(find_dotenv(".default.env", usecwd=True))
    load_dotenv(find_dotenv(".env", usecwd=True), override=True)
    fire.Fire(generate_target_agent)


if __name__ == "__main__":
    fire.Fire(main)
