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
    process_a2a_agent_response,
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

    # TODO: Remove this when streaming is available
    spinner_msg = cl.Message(content="⏳ Working on it...", author="assistant")
    await spinner_msg.send()

    message_id = uuid4()
    request_id = uuid4()

    request = create_message_request(
        message=message.content, context_id=context_id, request_id=request_id, message_id=message_id
    )

    try:
        result = await client.send_message(request, http_kwargs={"timeout": TIMEOUT})
        response = process_a2a_agent_response(result)

        if response.status == Status.COMPLETED:
            prepared_artifacts = prepare_agent_artifacts(response.model_dump())
            storage_backend = get_storage_backend()
            storage_backend.save(prepared_artifacts, DEFAULT_EXPORT_PATH / str(context_id))

        await cl.Message(
            content=response.message,
            author="assistant",
        ).send()

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
