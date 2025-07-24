import json
from typing import Any
from uuid import uuid4

import chainlit as cl
import chainlit.cli
import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard,
    MessageSendParams,
    SendMessageRequest,
)

from agent_factory.schemas import AgentFactoryOutputs
from agent_factory.utils import save_agent_outputs, setup_output_directory

PUBLIC_AGENT_CARD_PATH = "/.well-known/agent.json"
EXTENDED_AGENT_CARD_PATH = "/agent/authenticatedExtendedCard"

# Settings for the A2A server connection
HOST = "localhost"
PORT = 8080
BASE_URL = f"http://{HOST}:{PORT}"
TIMEOUT = 600  # 10 minutes


@cl.on_chat_start
async def on_chat_start():
    """Initialize the chat session"""
    cl.user_session.set("message_history", [])

    try:
        httpx_client = httpx.AsyncClient(timeout=TIMEOUT)
        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url=BASE_URL,
        )

        agent_card: AgentCard = await resolver.get_agent_card()
        client = A2AClient(httpx_client=httpx_client, agent_card=agent_card)

        context_id = str(uuid4())
        cl.user_session.set("a2a_client", client)
        cl.user_session.set("context_id", context_id)
        cl.user_session.set("timeout", TIMEOUT)

        await cl.Message(
            content=f"Connection to Agent at {BASE_URL} established. Ready to chat!",
            author="assistant",
        ).send()

    except Exception as e:
        await cl.Message(
            content=f"Failed to connect to agent server: {e}",
            author="Error",
        ).send()


@cl.on_message
async def on_message(message: cl.Message):
    """Handle incoming messages"""
    client = cl.user_session.get("a2a_client")
    context_id = cl.user_session.get("context_id")

    if not client:
        await cl.Message(
            content="A2A client not initialized. Please make sure the A2A server is running and restart the chat.",
            author="Error",
        ).send()
        return

    message_id = str(uuid4())
    send_message_payload: dict[str, Any] = {
        "message": {
            "role": "user",
            "parts": [{"kind": "text", "text": message.content}],
            "messageId": message_id,
            "contextId": context_id,
        },
    }

    request_id = str(uuid4())
    request = SendMessageRequest(id=request_id, params=MessageSendParams(**send_message_payload))

    try:
        result = await client.send_message(request, http_kwargs={"timeout": TIMEOUT})
        response_data = json.loads(result.root.result.status.message.parts[0].root.text)
        response = AgentFactoryOutputs(**response_data)

        if response.code_ready:
            output_dir = setup_output_directory()
            save_agent_outputs(response.model_dump(), output_dir)

        await cl.Message(
            content=response.answer,
            author="assistant",
        ).send()

    except Exception as e:
        await cl.Message(
            content=f"An error occurred: {e}",
            author="Error",
        ).send()


if __name__ == "__main__":
    chainlit.cli.run_chainlit(__file__)
