import json
from typing import Any
from uuid import uuid4

import chainlit as cl
import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard,
    MessageSendParams,
    SendMessageRequest,
)

PUBLIC_AGENT_CARD_PATH = "/.well-known/agent.json"
EXTENDED_AGENT_CARD_PATH = "/agent/authenticatedExtendedCard"


@cl.on_chat_start
async def on_chat_start():
    """Initialize the chat session"""
    cl.user_session.set("message_history", [])

    # Settings for the agent server connection
    host = "localhost"
    port = 8080
    timeout = 600
    base_url = f"http://{host}:{port}"

    try:
        httpx_client = httpx.AsyncClient(timeout=1500)
        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url=base_url,
        )

        agent_card: AgentCard = await resolver.get_agent_card()
        client = A2AClient(httpx_client=httpx_client, agent_card=agent_card)

        cl.user_session.set("a2a_client", client)
        cl.user_session.set("context_id", str(uuid4()))
        cl.user_session.set("timeout", timeout)

        await cl.Message(
            content=f"Connection to agent at {base_url} established. Ready to chat!",
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
    timeout = cl.user_session.get("timeout")

    if not client:
        await cl.Message(
            content="A2A client not initialized. Please restart the chat.",
            author="Error",
        ).send()
        return

    send_message_payload: dict[str, Any] = {
        "message": {
            "role": "user",
            "parts": [{"kind": "text", "text": message.content}],
            "messageId": str(uuid4()),
            "contextId": context_id,
        },
    }
    request = SendMessageRequest(id=str(uuid4()), params=MessageSendParams(**send_message_payload))

    try:
        result = await client.send_message(request, http_kwargs={"timeout": timeout})
        response = json.loads(result.root.result.status.message.parts[0].root.text)

        await cl.Message(
            content=response.get("answer", "No answer received."),
            author="assistant",
        ).send()

    except Exception as e:
        await cl.Message(
            content=f"An error occurred: {e}",
            author="Error",
        ).send()


if __name__ == "__main__":
    import chainlit.cli

    chainlit.cli.run_chainlit(__file__)
