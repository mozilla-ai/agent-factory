"""Utility functions for the A2A client."""

import json
from typing import Any
from uuid import UUID, uuid4

import httpx
from a2a.client import A2ACardResolver
from a2a.types import AgentCard, MessageSendParams, SendStreamingMessageRequest

from agent_factory.utils.logging import logger


async def create_a2a_http_client(host: str, port: int, timeout: int) -> tuple[httpx.AsyncClient, str]:
    """Create and return an HTTP client with base URL.

    Args:
        host: The host address for the agent server.
        port: The port for the agent server.
    """
    base_url = f"http://{host}:{port}"
    return httpx.AsyncClient(timeout=timeout), base_url


async def get_a2a_agent_card(resolver: A2ACardResolver) -> AgentCard:
    """Fetch the agent card from the resolver."""
    try:
        return await resolver.get_agent_card()
    except Exception as e:
        logger.error(f"Critical error fetching public agent card: {e}", exc_info=True)
        raise RuntimeError("Failed to fetch the public agent card. Cannot continue.") from e


def create_message_request(
    message: str, context_id: UUID | None = None, request_id: UUID | None = None, message_id: UUID | None = None
) -> SendStreamingMessageRequest:
    """Create a message request to send to the agent."""
    send_message_payload: dict[str, Any] = {
        "message": {
            "role": "user",
            "parts": [{"kind": "text", "text": message}],
            "messageId": message_id.hex if message_id else uuid4().hex,
            "contextId": context_id.hex if context_id else uuid4().hex,
        },
    }
    return SendStreamingMessageRequest(
        id=request_id.hex if request_id else uuid4().hex, params=MessageSendParams(**send_message_payload)
    )


def process_a2a_agent_response(response: Any) -> dict:
    """Process the response from the agent."""
    logger.info(response.model_dump(mode="json", exclude_none=True))
    result = json.loads(response.root.result.status.message.parts[0].root.text)
    logger.info(f"Received response from agent: {result}")
    return result
