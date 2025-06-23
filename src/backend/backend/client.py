import asyncio
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

from backend.settings import settings

BASE_URL = settings.A2A_AGENT_URL
PUBLIC_AGENT_CARD_PATH = settings.PUBLIC_AGENT_CARD_PATH
EXTENDED_AGENT_CARD_PATH = settings.EXTENDED_AGENT_CARD_PATH


class AgentClient:
    def __init__(self, base_url: str, httpx_client: httpx.AsyncClient):
        self.base_url = base_url
        self.httpx_client = httpx_client
        self.client: A2AClient | None = None

    async def _connect(self) -> None:
        if self.client:
            return

        print(f"Connecting to agent at {self.base_url}...")
        try:
            resolver = A2ACardResolver(self.httpx_client, self.base_url)
            agent_card: AgentCard = await resolver.get_agent_card(http_kwargs=None)
            self.client = A2AClient(httpx_client=self.httpx_client, agent_card=agent_card)
            print("Connection successful.")
        except Exception as e:
            print(f"Failed to connect to agent at {self.base_url}: {e}")
            raise

    async def send_message(self, message_text: str, timeout: int = 60) -> SendMessageResponse | None:
        # Ensure the client is connected before sending a message.
        if not self.client:
            await self._connect()

        if not self.client:
            print("Cannot send message: client not initialized.")
            return None

        send_message_payload: dict[str, Any] = {
            "message": {
                "role": "user",
                "parts": [{"kind": "text", "text": message_text}],
                "messageId": uuid4().hex,
            },
        }

        request = SendMessageRequest(id=str(uuid4()), params=MessageSendParams(**send_message_payload))
        response = await self.client.send_message(request, http_kwargs={"timeout": timeout})
        return response


async def main():
    async with httpx.AsyncClient() as httpx_client:
        message_to_send = "Summarize a URL."

        agent = AgentClient(base_url="http://localhost:5001", httpx_client=httpx_client)
        try:
            response = await agent.send_message(message_to_send)
            if response:
                print(f"\nResponse from first agent ({agent.base_url}):")
                print(response.model_dump_json(indent=2))
        except Exception as e:
            print(f"Error communicating with agent 1: {e}")


if __name__ == "__main__":
    asyncio.run(main())
