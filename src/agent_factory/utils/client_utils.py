"""Utility functions for the A2A client."""

import json
from typing import Any
from uuid import uuid4

import httpx
from a2a.client import A2ACardResolver
from a2a.types import AgentCard, MessageSendParams, SendMessageRequest

from agent_factory.utils.logging import logger


async def create_a2a_http_client(host: str, port: int) -> tuple[httpx.AsyncClient, str]:
    """Create and return an HTTP client with base URL.

    Args:
        host: The host address for the agent server.
        port: The port for the agent server.
    """
    base_url = f"http://{host}:{port}"
    return httpx.AsyncClient(), base_url


async def get_a2a_agent_card(resolver: A2ACardResolver) -> AgentCard:
    """Fetch the agent card from the resolver."""
    try:
        return await resolver.get_agent_card()
    except Exception as e:
        logger.error(f"Critical error fetching public agent card: {e}", exc_info=True)
        raise RuntimeError("Failed to fetch the public agent card. Cannot continue.") from e


def create_message_request(message: str) -> SendMessageRequest:
    """Create a message request to send to the agent."""
    send_message_payload = {
        "message": {
            "role": "user",
            "parts": [{"kind": "text", "text": message}],
            "messageId": uuid4().hex,
        },
    }
    return SendMessageRequest(id=str(uuid4()), params=MessageSendParams(**send_message_payload))


def process_a2a_agent_response(response: Any) -> dict:
    """Process the response from the agent."""
    logger.info(response.model_dump(mode="json", exclude_none=True))
    result = json.loads(response.root.result.status.message.parts[0].root.text)
    logger.info(f"Received response from agent: {result}")
    return result
