import json
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
from rich.console import Console
from rich.markdown import Markdown
from utils.logging import logger

PUBLIC_AGENT_CARD_PATH = "/.well-known/agent.json"
EXTENDED_AGENT_CARD_PATH = "/agent/authenticatedExtendedCard"


async def main(host: str = "localhost", port: int = 8080, timeout: int = 600) -> None:
    """Main entry point for the A2A client application.

    Args:
        message (str): The message to send to the agent.
        host (str): The host address for the agent server (default: "localhost").
        port (int): The port for the agent server (default: 8080).
        timeout (str): The timeout for the request in seconds (default: 600).
    """
    base_url = f"http://{host}:{port}"

    async with httpx.AsyncClient(timeout=1500) as httpx_client:
        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url=base_url,
        )

        agent_card: AgentCard = await resolver.get_agent_card()
        client = A2AClient(httpx_client=httpx_client, agent_card=agent_card)

        context_id = str(uuid4())

        while True:
            prompt = input("\nEnter your message (or 'exit' to quit): ")
            if prompt.lower() == "exit":
                logger.info("Exiting the client.")
                break
            elif not prompt.strip():
                logger.warning("Empty message received. Please enter a valid message.")
                continue
            send_message_payload: dict[str, Any] = {
                "message": {
                    "role": "user",
                    "parts": [{"kind": "text", "text": prompt}],
                    "messageId": str(uuid4()),
                    "contextId": context_id,
                },
            }
            request = SendMessageRequest(id=str(uuid4()), params=MessageSendParams(**send_message_payload))
            result = await client.send_message(request, http_kwargs={"timeout": timeout})
            response = json.loads(result.root.result.status.message.parts[0].root.text)
            console = Console()
            md = Markdown(response["answer"])
            print()
            console.print(md)


if __name__ == "__main__":
    fire.Fire(main)
