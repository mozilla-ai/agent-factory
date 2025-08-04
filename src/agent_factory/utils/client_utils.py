"""Utility functions for the A2A client."""

import json
from typing import Any
from uuid import UUID, uuid4

import httpx
from a2a.client import A2ACardResolver
from a2a.types import AgentCard, MessageSendParams, SendMessageRequest

from agent_factory.schemas import AgentFactoryOutputs
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
) -> SendMessageRequest:
    """Create a message request to send to the agent."""
    if not request_id:
        logger.info("No request ID provided, generating a new one")
        request_id = uuid4()
    elif isinstance(request_id, str):
        try:
            request_id = UUID(request_id)
        except (ValueError, AttributeError):
            logger.warning(f"Invalid UUID string: {request_id}, generating a new one")
            request_id = uuid4()
    logger.info(f"Request ID: {request_id}")

    send_message_payload: dict[str, Any] = {
        "message": {
            "role": "user",
            "parts": [{"kind": "text", "text": message}],
            "messageId": message_id.hex if message_id else uuid4().hex,
            "contextId": context_id.hex if context_id else uuid4().hex,
        },
    }
    return SendMessageRequest(id=request_id.hex, params=MessageSendParams(**send_message_payload))


def process_a2a_agent_response(response: Any) -> AgentFactoryOutputs:
    """Process the response from the agent."""
    logger.info(response.model_dump(mode="json", exclude_none=True))
    response_data = json.loads(response.root.result.status.message.parts[0].root.text)
    logger.info(f"Received response from agent: {response_data}")
    return AgentFactoryOutputs(**response_data)
