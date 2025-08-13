import asyncio
import json
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
from agent_factory.utils.client_utils import ProcessedStreamingResponse

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


class ThinkingMessageUpdater:
    """Handle streaming "thinking" messages with an animated spinner."""

    def __init__(self, message: cl.Message):
        self.author = message.author
        self.last_sent_content: ProcessedStreamingResponse | None = None
        self.current_content = ProcessedStreamingResponse(message="Thinking…")

        self.spinner_frames = ["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"]
        self._spinner_index = 0

        self.current_msg: cl.Message | None = None  # Message currently showing spinner

        self._should_stop = False
        self._last_update_time = 0
        self._update_interval = 2  # Minimum seconds between updates

    async def update_loop(self):
        """Send/animate thinking messages with a live spinner on the latest one."""
        while not self._should_stop:
            current_time = asyncio.get_event_loop().time()

            # Only send update if content changed and enough time has passed
            if (
                self.current_content != self.last_sent_content
                and current_time - self._last_update_time >= self._update_interval
            ):
                # Finalise previous spinner message (replace animated icon with static one)
                if self.current_msg:
                    static_txt = self._render_message(self.last_sent_content, spinner_char="✅")
                    self.current_msg.content = static_txt
                    await self.current_msg.update()

                # Create new spinner message
                spinner_txt = self._render_message(self.current_content, spinner_char=self.spinner_frames[0])
                self.current_msg = cl.Message(content=spinner_txt, author=self.author)
                await self.current_msg.send()

                self.last_sent_content = self.current_content
                self._last_update_time = current_time
                self._spinner_index = 1

            if self.current_msg and not self._should_stop:
                spinner_char = self.spinner_frames[self._spinner_index % len(self.spinner_frames)]
                anim_txt = self._render_message(self.last_sent_content, spinner_char=spinner_char)
                self.current_msg.content = anim_txt
                await self.current_msg.update()
                self._spinner_index += 1

            await asyncio.sleep(0.1)

    def _render_message(self, content: ProcessedStreamingResponse, *, spinner_char: str) -> str:
        """Return formatted message string with given spinner/static icon."""
        text = f"{spinner_char} {content.message}"
        if content.message_attributes:
            json_str = json.dumps(content.message_attributes, indent=2, ensure_ascii=False)
            text += f"\n```json\n{json_str}\n```"
        return text

    def update_content(self, new_content: ProcessedStreamingResponse):
        """Update the content that will be used for the next message."""
        self.current_content = new_content

    def stop(self):
        """Signal the update loop to stop and finalize the last spinner message."""
        self._should_stop = True
        if self.current_msg:
            static_txt = self._render_message(self.last_sent_content, spinner_char="✅")
            self.current_msg.content = static_txt
            asyncio.create_task(self.current_msg.update())


async def create_agent(message: cl.Message):
    client = cl.user_session.get("a2a_client")
    context_id = cl.user_session.get("context_id")

    if not client:
        await cl.Message(
            content="A2A client not initialized. Please make sure the A2A server is running and restart the chat.",
            author="Error",
        ).send()
        return

    # Create and start the message updater
    msg = cl.Message(content="", author="assistant")
    thinking_message_updater = ThinkingMessageUpdater(msg)
    thinking_message_update_task = asyncio.create_task(thinking_message_updater.update_loop())

    message_id = uuid4()
    request_id = uuid4()

    request = create_message_request(
        message=message.content, context_id=context_id, request_id=request_id, message_id=message_id
    )

    try:
        responses = []
        async for response in client.send_message_streaming(request, http_kwargs={"timeout": TIMEOUT}):
            processed_response = process_streaming_response_message(response)
            if processed_response.message:
                thinking_message_updater.update_content(processed_response)
            responses.append(response)

        # We can stop the update task and clean up
        thinking_message_updater.stop()
        await thinking_message_update_task

        if responses:
            final_response = responses[-1]
            final_response = process_a2a_agent_final_response(final_response)

            if final_response.status == Status.COMPLETED:
                prepared_artifacts = prepare_agent_artifacts(final_response.model_dump())
                storage_backend = get_storage_backend()
                storage_backend.save(prepared_artifacts, DEFAULT_EXPORT_PATH / str(context_id))

            if final_response.message:
                await cl.Message(content=final_response.message, author="assistant").send()

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
            content=f"Connection to Agent at {base_url}{PUBLIC_AGENT_CARD_PATH} established. Ready to chat!",
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
