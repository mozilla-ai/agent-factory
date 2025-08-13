"""Utility functions for the A2A client."""

import json
from typing import Any, Literal
from uuid import UUID, uuid4

import httpx
from a2a.client import A2ACardResolver
from a2a.types import AgentCard, MessageSendParams, SendStreamingMessageRequest, TaskState
from any_agent.tracing.attributes import GenAI
from pydantic import BaseModel

from agent_factory.schemas import AgentFactoryOutputs
from agent_factory.utils.logging import logger


class ProcessedStreamingResponse(BaseModel):
    message_type: Literal["info", "error"] = "info"
    message: str | None = None
    message_attributes: dict[str, Any] = {}


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
    if not message or not message.strip():
        raise ValueError("Message cannot be empty or whitespace only")
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
    return SendStreamingMessageRequest(id=request_id.hex, params=MessageSendParams(**send_message_payload))


def process_a2a_agent_final_response(response: Any) -> AgentFactoryOutputs:
    """Process the final response from the agent."""
    logger.info(response.model_dump(mode="json", exclude_none=True))
    response_data = json.loads(response.root.result.status.message.parts[0].root.text)
    logger.info(f"Received response from agent: {response_data}")
    return AgentFactoryOutputs(**response_data)


def process_streaming_response_message(response: Any) -> ProcessedStreamingResponse:
    """Process an agent response message and return a structured response.

    Args:
        response: The response object from the A2A agent.

    Returns:
        A ProcessedStreamingResponse object containing the message type,
        message content, and any additional attributes.
    """
    try:
        processed_response = ProcessedStreamingResponse()

        # TastState is an enum with values:
        # submitted, working, completed, failed, input-required, canceled, unknown
        # See: https://www.a2aprotocol.net/docs/specification
        # Using a subset of these states to log different messages
        if response.root.result.status.state == TaskState.submitted:
            processed_response.message = "Manufacturing agent has received the message and is processing it."

        elif response.root.result.status.state == TaskState.working and response.root.result.status.message:
            message_data = response.root.result.status.message.parts[0].root.data
            if message_data.get("event_type") == "tool_started" and "payload" in message_data:
                tool_call_info_to_log = {
                    k: v
                    for k, v in message_data["payload"].items()
                    if k in [GenAI.OPERATION_NAME, GenAI.TOOL_NAME, GenAI.TOOL_ARGS]
                }
                processed_response.message = "Making a tool call ..."
                processed_response.message_attributes = tool_call_info_to_log

        elif response.root.result.status.state == TaskState.completed:
            processed_response.message = "Manufacturing agent has completed the assigned task."

        return processed_response

    except Exception as e:
        processed_response = ProcessedStreamingResponse(
            message_type="error",
            message=f"Error processing response: {str(e)}",
            message_attributes={"error": str(e)},
        )
        return processed_response


def is_server_live(host: str, port: int, timeout: float = 2.0) -> bool:
    """Check if the server at the given host and port is live by attempting a TCP connection.
    Returns True if connection is successful, False otherwise.
    """
    import socket

    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (OSError, ConnectionRefusedError, TimeoutError):
        return False
