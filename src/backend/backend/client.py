from typing import Any
from uuid import uuid4

import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard,
    MessageSendParams,
    SendMessageRequest,
    SendMessageResponse,
)

from backend.logging import logger


class AgentClient:
    """A client for interacting with an A2A agent.

    This client handles the connection to the agent, sending messages, and
    receiving responses.

    Attributes:
        base_url (str): The base URL of the A2A agent.
        httpx_client (httpx.AsyncClient): The HTTP client used for making requests.
        client (A2AClient | None): The A2AClient instance for communication with
            the agent, initialized to None until connected.
    """

    def __init__(self, base_url: str, httpx_client: httpx.AsyncClient):
        self.base_url = base_url
        self.httpx_client = httpx_client
        self.client: A2AClient | None = None

    async def send_message(self, message_text: str, timeout: int = 60) -> SendMessageResponse | None:
        """Sends a message to the A2A agent and returns the response.

        Args:
            message_text (str): The text of the message to send to the agent.
            timeout (int): The timeout for the request in seconds. Defaults to 60 seconds.

        Returns:
            SendMessageResponse | None: The response from the agent, or None if the request fails
        """
        logger.info(f"Connecting to agent at {self.base_url}...")
        if not self.client:
            resolver = A2ACardResolver(self.httpx_client, self.base_url)
            agent_card: AgentCard = await resolver.get_agent_card(http_kwargs=None)
            logger.info(agent_card.model_dump_json(indent=2, exclude_none=True))

            # Initialize the A2AClient with a URL instead of an agent card
            # because the agent card advertises that the agent is available on localhost.
            self.client = A2AClient(httpx_client=self.httpx_client, url=self.base_url)
            logger.info("Connection successful.")

        send_message_payload: dict[str, Any] = {
            "message": {
                "role": "user",
                "parts": [{"kind": "text", "text": message_text}],
                "messageId": uuid4().hex,
            },
        }

        logger.info(f"Sending message to agent: {send_message_payload}")

        request = SendMessageRequest(id=str(uuid4()), params=MessageSendParams(**send_message_payload))
        response = await self.client.send_message(request, http_kwargs={"timeout": timeout})
        return response
