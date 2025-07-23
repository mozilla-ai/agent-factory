from pathlib import Path

import fire
from a2a.client import A2ACardResolver, A2AClient

from agent_factory.utils import (
    create_a2a_http_client,
    create_message_request,
    get_a2a_agent_card,
    process_a2a_agent_response,
    save_agent_outputs,
    setup_output_directory,
)
from agent_factory.utils.logging import logger

PUBLIC_AGENT_CARD_PATH = "/.well-known/agent.json"
EXTENDED_AGENT_CARD_PATH = "/agent/authenticatedExtendedCard"


async def generate(
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
    http_client, base_url = await create_a2a_http_client(host, port)
    async with http_client as client:
        resolver = A2ACardResolver(httpx_client=client, base_url=base_url)
        agent_card = await get_a2a_agent_card(resolver)

        # Initialize client and send message
        client = A2AClient(httpx_client=client, agent_card=agent_card)
        logger.info("A2AClient initialized.")

        request = create_message_request(message)
        response = await client.send_message(request, http_kwargs={"timeout": timeout})

        # Process response
        result = process_a2a_agent_response(response)
        output_dir = setup_output_directory(output_dir)
        save_agent_outputs(result, output_dir)


def main():
    fire.Fire(generate)


if __name__ == "__main__":
    fire.Fire(main)
