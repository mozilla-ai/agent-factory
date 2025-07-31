from pathlib import Path

import fire
from a2a.client import A2ACardResolver, A2AClient

from agent_factory.schemas import Status
from agent_factory.utils import (
    create_a2a_http_client,
    create_message_request,
    get_a2a_agent_card,
    process_a2a_agent_response,
    setup_output_directory,
)
from agent_factory.utils.logging import logger
from agent_factory.utils.storage import get_storage_backend

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
            output_dir = setup_output_directory(output_dir)
            storage_backend = get_storage_backend()
            storage_backend.save(response.model_dump(), output_dir)
        elif response.status == Status.INPUT_REQUIRED:
            logger.info(
                f"Please try again and be more specific with your request. Agent's response: {response.message}"
            )
        else:
            logger.error(f"Agent encountered an error: {response.message}")


def main():
    fire.Fire(generate_target_agent)


if __name__ == "__main__":
    fire.Fire(main)
