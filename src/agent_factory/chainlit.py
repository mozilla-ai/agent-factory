import asyncio
import contextlib
from uuid import uuid4

import chainlit as cl
import chainlit.cli
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard,
)

from agent_factory.config import DEFAULT_EXPORT_PATH
from agent_factory.schemas import Status
from agent_factory.utils import (
    create_a2a_http_client,
    create_message_request,
    get_a2a_agent_card,
    get_storage_backend,
    prepare_agent_artifacts,
    process_a2a_agent_final_response,
    process_streaming_response_message,
)

PUBLIC_AGENT_CARD_PATH = "/.well-known/agent.json"
EXTENDED_AGENT_CARD_PATH = "/agent/authenticatedExtendedCard"

# Settings for the A2A server connection
HOST = "localhost"
PORT = 8080
TIMEOUT = 600  # 10 minutes

COMMANDS = [
    {"id": "create", "icon": "bot", "description": "Create an AI Agent"},
    {"id": "edit", "icon": "pencil", "description": "Edit an existing AI Agent"},
]


async def create_agent(message: cl.Message):
    client = cl.user_session.get("a2a_client")
    context_id = cl.user_session.get("context_id")

    if not client:
        await cl.Message(
            content="A2A client not initialized. Please make sure the A2A server is running and restart the chat.",
            author="Error",
        ).send()
        return

    # Animated spinner while the agent is working
    spinner_msg = cl.Message(content="⏳ Thinking...", author="assistant")
    await spinner_msg.send()

    async def animate_spinner(msg: cl.Message):
        """Continuously update the spinner message until cancelled."""
        spinner_frames = ["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"]
        i = 0
        try:
            while True:
                msg.content = f"{spinner_frames[i % len(spinner_frames)]} Thinking..."
                await msg.update()
                i += 1
                await cl.sleep(0.1)
        except asyncio.CancelledError:
            # Clear spinner when cancelled
            pass

    spinner_task = asyncio.create_task(animate_spinner(spinner_msg))

    message_id = uuid4()
    request_id = uuid4()

    request = create_message_request(
        message=message.content, context_id=context_id, request_id=request_id, message_id=message_id
    )

    try:
        msg = cl.Message(content="", author="assistant")
        await msg.send()

        responses = []
        async for response in client.send_message_streaming(request, http_kwargs={"timeout": TIMEOUT}):
            text, _ = process_streaming_response_message(response)
            if text:
                msg.content = text
                await msg.update()
            responses.append(response)

        # Stop spinner
        spinner_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await spinner_task
        await spinner_msg.remove()

        if responses:
            final_response = responses[-1]
            final_response = process_a2a_agent_final_response(final_response)
            if final_response.status == Status.COMPLETED:
                prepared_artifacts = prepare_agent_artifacts(final_response.model_dump())
                storage_backend = get_storage_backend()
                storage_backend.save(prepared_artifacts, DEFAULT_EXPORT_PATH / str(context_id))
            msg.content = final_response.message
            await msg.update()

    except Exception as e:
        await cl.Message(
            content=f"An error occurred: {e}",
            author="Error",
        ).send()


@cl.on_chat_start
async def on_chat_start():
    """Initialize the chat session"""
    # Set up the commands for the chat interface
    # This can be extended with more commands as needed, to capture user intent in a deterministic way
    await cl.context.emitter.set_commands(COMMANDS)  # type: ignore

    cl.user_session.set("message_history", [])

    try:
        httpx_client, base_url = await create_a2a_http_client(HOST, PORT, TIMEOUT)
        resolver = A2ACardResolver(httpx_client=httpx_client, base_url=base_url)

        agent_card: AgentCard = await get_a2a_agent_card(resolver)
        client = A2AClient(httpx_client=httpx_client, agent_card=agent_card)

        context_id = uuid4()
        cl.user_session.set("a2a_client", client)
        cl.user_session.set("context_id", context_id)
        cl.user_session.set("timeout", TIMEOUT)

        await cl.Message(
            content=f"Connection to Agent at {base_url} established. Ready to chat!",
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
    if message.command == "create":
        await create_agent(message)
    elif message.command == "edit":
        await cl.Message(
            content="Editing agents is not yet implemented. Please use `/create` to create a new agent.",
            author="assistant",
        ).send()
    else:
        await create_agent(message)


if __name__ == "__main__":
    from dotenv import find_dotenv, load_dotenv

    load_dotenv(find_dotenv(".default.env", usecwd=True))
    load_dotenv(find_dotenv(".env", usecwd=True), override=True)
    chainlit.cli.run_chainlit(__file__)
