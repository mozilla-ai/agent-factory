import json
import uuid
from datetime import datetime
from pathlib import Path

import chainlit as cl
from any_agent import AgentConfig, AgentFramework, AnyAgent
from any_agent.config import MCPStdio
from dotenv import load_dotenv
from src.instructions import INSTRUCTIONS
from src.main import (
    AgentFactoryOutputs,
    archive_latest_run_artifacts,
    build_run_instructions,
    get_default_tools,
    save_agent_parsed_outputs,
    setup_directories,
)

load_dotenv()

repo_root = Path.cwd()
workflows_root = repo_root / "generated_workflows"
tools_dir = repo_root / "tools"
mcps_dir = repo_root / "mcps"

MCP_TOOLS = []


def get_mount_config():
    return {
        "host_workflows_dir": str(workflows_root),
        "host_tools_dir": str(tools_dir),
        "host_mcps_dir": str(mcps_dir),
        "container_workflows_dir": "/app/generated_workflows",
        "container_tools_dir": "/app/tools",
        "container_mcps_dir": "/app/mcps",
        "file_ops_dir": "/app",
    }


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

            # Get mount config and default tools
            mount_config = get_mount_config()
            tools = get_default_tools(mount_config)

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
                    instructions=INSTRUCTIONS,
                    tools=tools,
                ),
            )

            # Trim context and format conversation
            trimmed_history = trim_context(message_history, max_messages=10)
            conversation = format_messages_for_agent(trimmed_history)

            # Build task
            task = build_run_instructions(conversation)

            step.output = "Running agent with your request..."

            # Run the agent
            agent_factory_trace = agent_factory.run(task, max_turns=30)

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
            json_output = json.loads(agent_factory_trace.final_output)
            output_to_render = (
                f"## 🤖 Agent Code\n"
                f"```python\n{json_output.get('agent_code', 'No agent code provided.')}\n```\n"
                f"## 🚀 Run Instructions\n"
                f"{json_output.get('run_instructions', 'No run instructions provided.')}\n\n"
                f"## 📦 Dependencies\n"
                f"```\n{json_output.get('dependencies', 'No dependencies provided.')}\n```"
            )

            # Add export button action
            actions = [
                cl.Action(
                    name="export_workflow",
                    payload=json_output,
                    tooltip="Export the generated agent code, instructions, and dependencies to generated_workflows/latest directory.",  # noqa: E501
                    label="📁 Save Workflow to Files",
                    icon="download",
                )
            ]
            response_msg = cl.Message(content=output_to_render, author="assistant", actions=actions)
            await response_msg.send()

            # Add assistant response to history
            message_history.append({"role": "assistant", "content": output_to_render})

        # Update session with new message history
        cl.user_session.set("message_history", message_history)

    except Exception as e:
        await cl.Message(content=f"❌ **Error occurred:** {str(e)}", author="Error").send()


@cl.action_callback("export_workflow")
async def export_workflow_action(action: cl.Action):
    """Handle export workflow button click: validate and save agent outputs."""
    latest_dir, archive_root = setup_directories(workflows_root, workflows_root / "latest")
    workflow_id = str(uuid.uuid4())
    timestamp_id = datetime.now().strftime("%Y-%m-%d_%H:%M:%S") + "_" + workflow_id[:8]
    archive_dir = archive_root / timestamp_id
    archive_dir.mkdir(parents=True, exist_ok=True)
    try:
        agent_factory_outputs = AgentFactoryOutputs.model_validate(action.payload)
        save_agent_parsed_outputs(agent_factory_outputs, "latest")
        archive_latest_run_artifacts(latest_dir, archive_dir)
        await cl.Message(
            content="✅ Workflow exported successfully to the 'generated_workflows/latest' directory.",
            author="assistant",
        ).send()
    except Exception as e:
        await cl.Message(content=f"❌ Failed to export workflow: {e}", author="Error").send()


if __name__ == "__main__":
    import chainlit.cli

    chainlit.cli.run_chainlit(__file__)
