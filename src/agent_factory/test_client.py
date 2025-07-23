import json
from pathlib import Path
from typing import Any
from uuid import uuid4

import fire
import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard,
    MessageSendParams,
    SendMessageRequest,
)

from agent_factory.utils import logger, save_agent_outputs, setup_output_directory

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
        message (str): The message to send to the agent.
        host (str): The host address for the agent server (default: "localhost").
        port (int): The port for the agent server (default: 8080).
        timeout (str): The timeout for the request in seconds (default: 600).
    """
    base_url = f"http://{host}:{port}"

    async with httpx.AsyncClient() as httpx_client:
        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url=base_url,
        )

        try:
            agent_card: AgentCard = await resolver.get_agent_card()
        except Exception as e:
            logger.error(f"Critical error fetching public agent card: {e}", exc_info=True)
            raise RuntimeError("Failed to fetch the public agent card. Cannot continue.") from e

        client = A2AClient(httpx_client=httpx_client, agent_card=agent_card)
        logger.info("A2AClient initialized.")

        send_message_payload: dict[str, Any] = {
            "message": {
                "role": "user",
                "parts": [{"kind": "text", "text": message}],
                "messageId": uuid4().hex,
            },
        }
        request = SendMessageRequest(id=str(uuid4()), params=MessageSendParams(**send_message_payload))

        response = await client.send_message(request, http_kwargs={"timeout": timeout})
        logger.info(response.model_dump(mode="json", exclude_none=True))

        result = json.loads(response.root.result.status.message.parts[0].root.text)
        logger.info(f"Received response from agent: {result}")

        output_dir = setup_output_directory(output_dir)
        save_agent_outputs(result, output_dir)


def main():
    fire.Fire(generate)


if __name__ == "__main__":
    fire.Fire(main)
