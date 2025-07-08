import json
from pathlib import Path

import chainlit as cl
import dotenv
from any_agent import AgentConfig, AgentFramework, AnyAgent
from any_agent.config import MCPStdio
from any_agent.tools import search_tavily, visit_webpage

from agent.factory_tools import read_file, search_mcp_servers
from agent.instructions import AGENT_CODE_TEMPLATE, AGENT_CODE_TEMPLATE_RUN_VIA_CLI, load_system_instructions
from agent.schemas import AgentFactoryOutputs
from agent_factory.generation import (
    build_run_instructions,
    save_agent_outputs,
)

dotenv.load_dotenv()

repo_root = Path.cwd()
workflows_root = repo_root / "generated_workflows"
tools_dir = repo_root / "tools"

MCP_TOOLS = []


def trim_context(conversation_history, max_messages=10):
    """Trim conversation history to stay within max message count."""
    if len(conversation_history) > max_messages:
        return conversation_history[-max_messages:]
    return conversation_history


def format_messages_for_agent(messages: list) -> str:
    """Convert message history to conversation string for the agent"""
    conversation = ""
    for msg in messages:
        role = "User" if msg["role"] == "user" else "Assistant"
        conversation += f"{role}: {msg['content']}\n\n"
    return conversation


@cl.on_mcp_connect
async def on_mcp_connect(connection, session):
    """Called when an MCP connection is established"""
    MCP_TOOLS.append(connection)


@cl.on_mcp_disconnect
async def on_mcp_disconnect(name: str, session):
    """Called when an MCP connection is terminated"""
    # Remove the disconnected tool
    MCP_TOOLS[:] = [tool for tool in MCP_TOOLS if tool != session]


@cl.on_chat_start
async def on_chat_start():
    """Initialize the chat session"""
    cl.user_session.set("message_history", [])

    # Send welcome message
    await cl.Message(
        content="👋 Welcome! I'm ready to help you create and run agentic workflows. Describe the workflow you want to build:",  # noqa: E501
        author="assistant",
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    """Handle incoming messages"""
    try:
        # Get message history from session
        message_history = cl.user_session.get("message_history", [])

        # Add user message to history
        message_history.append({"role": "user", "content": message.content})

        # Show thinking indicator
        async with cl.Step(name="any-agent to generate your workflow", type="run") as step:
            step.output = "Analyzing your request and preparing the agent..."

            tools = [visit_webpage, search_tavily, search_mcp_servers, read_file]
            # Register existing MCP tools (if any)
            if MCP_TOOLS:
                for tool in MCP_TOOLS:
                    if getattr(tool, "clientType", None) == "stdio":
                        mcp_tool = MCPStdio(command=tool.command, args=tool.args, env=getattr(tool, "env", None))
                        tools.append(mcp_tool)

            # Create agent
            framework = AgentFramework.OPENAI
            agent_factory = AnyAgent.create(
                framework,
                AgentConfig(
                    model_id="o3",
                    instructions=load_system_instructions(),
                    tools=tools,
                    output_type=AgentFactoryOutputs,
                ),
            )

            # Trim context and format conversation
            trimmed_history = trim_context(message_history, max_messages=10)
            conversation = format_messages_for_agent(trimmed_history)

            # Build task
            task = build_run_instructions(conversation)

            step.output = "Running agent with your request..."

            # Run the synchronous agent function in a separate thread
            # This prevents blocking the main asyncio event loop.
            agent_factory_run = cl.make_async(agent_factory.run)
            agent_factory_trace = await agent_factory_run(task, max_turns=30)

        # Display tool usage information
        if hasattr(agent_factory_trace, "spans"):
            for span in agent_factory_trace.spans:
                tool_usage = span.attributes.get("gen_ai.tool.args", "")
                try:
                    # Attempt to parse and pretty-print JSON
                    formatted_content = json.dumps(json.loads(tool_usage), indent=4)
                    content_to_display = f"⚙️ Used: **{span.name}**:\n```json\n{formatted_content}\n```"
                except (json.JSONDecodeError, TypeError):
                    # Fallback to raw string if not valid JSON
                    content_to_display = f"⚙️ Used: **{span.name}**"

                await cl.Message(
                    content=content_to_display,
                    author="Agent Steps",
                ).send()

        # Send the final response
        if agent_factory_trace.final_output:
            json_output = agent_factory_trace.final_output.model_dump()
            agent_code = (
                f"{AGENT_CODE_TEMPLATE.format(**agent_factory_trace.final_output.model_dump())} \n"
                f"{AGENT_CODE_TEMPLATE_RUN_VIA_CLI.format(**agent_factory_trace.final_output.model_dump())}"
            )
            output_to_render = (
                f"## 🤖 Agent Code\n"
                f"```python\n{agent_code}\n```\n"
                f"## 📚 README\n"
                f"{json_output.get('readme', 'No README provided.')}\n\n"
                f"## 📦 Dependencies\n"
                f"```\n{json_output.get('dependencies', 'No dependencies provided.')}\n```"
            )

            # Add export button action
            actions = [
                cl.Action(
                    name="export_workflow",
                    payload=json_output,
                    tooltip="Export the generated agent code, README, and dependencies to generated_workflows/latest directory.",  # noqa: E501
                    label="📁 Save Workflow to Files",
                    icon="download",
                )
            ]
            response_msg = cl.Message(content=output_to_render, author="assistant", actions=actions)
            await response_msg.send()

            # Add assistant response to history
            message_history.append({"role": "assistant", "content": output_to_render})

        # Handle the case where the agent finishes without providing an output
        else:
            await cl.Message(
                content="The agent finished its run but did not produce a final output.", author="assistant"
            ).send()

        # Update session with new message history
        cl.user_session.set("message_history", message_history)

    except Exception as e:
        await cl.Message(content=f"❌ **Error occurred:** {str(e)}", author="Error").send()


@cl.action_callback("export_workflow")
async def export_workflow_action(action: cl.Action):
    """Handle export workflow button click: validate and save agent outputs."""
    output_dir = Path("generated_workflows") / "latest"
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        agent_factory_outputs = AgentFactoryOutputs.model_validate(action.payload)
        save_agent_outputs(agent_factory_outputs, output_dir)
        await cl.Message(
            content="✅ Workflow exported successfully to 'generated_workflows/latest'.",
            author="assistant",
        ).send()
    except Exception as e:
        await cl.Message(content=f"❌ Failed to export workflow: {e}", author="Error").send()


if __name__ == "__main__":
    import chainlit.cli

    chainlit.cli.run_chainlit(__file__)
