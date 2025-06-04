from pathlib import Path

import chainlit as cl
from any_agent import AgentConfig, AgentFramework, AnyAgent
from any_agent.config import MCPStdio
from dotenv import load_dotenv
from src.instructions import INSTRUCTIONS
from src.main import build_run_instructions, get_default_tools

load_dotenv()

repo_root = Path.cwd()
workflows_root = repo_root / "generated_workflows"
tools_dir = repo_root / "tools"
mcps_dir = repo_root / "mcps"

MCP_TOOLS = []
messages = []


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


def format_messages(all_cl_messages: list[cl.Message]):
    """Convert Chainlit messages to OpenAI format (list of dicts with role/content)"""
    if not all_cl_messages:
        return []
    formatted = []
    for msg in all_cl_messages:
        # Determine role: if author is 'Agent Steps' or 'assistant', treat as assistant; else user
        if getattr(msg, "author", None) in ["Agent Steps", "assistant"]:
            role = "assistant"
        else:
            role = "user"
        formatted.append({"role": role, "content": msg.content})
    return formatted


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
    cl.user_session.set("messages", [])


@cl.on_message
async def on_message(message: cl.Message):
    try:
        messages = cl.user_session.get("messages")
        # Append user message with correct role
        message.author = "user"
        messages.append(message)
        cl.user_session.set("messages", messages)

        # Get mount config and default tools
        mount_config = get_mount_config()
        tools = get_default_tools(mount_config)

        # Register existing MCP tools (if any)
        if MCP_TOOLS:
            for tool in MCP_TOOLS:
                if getattr(tool, "clientType", None) == "stdio":
                    mcp_tool = MCPStdio(command=tool.command, args=tool.args, env=getattr(tool, "env", None))
                    tools.append(mcp_tool)

        # Create agent with model_id, INSTRUCTIONS, tools
        framework = AgentFramework.OPENAI
        agent = AnyAgent.create(
            framework,
            AgentConfig(
                model_id="gpt-4.1",
                instructions=INSTRUCTIONS,
                tools=tools,
            ),
        )

        # Maintain conversation history (trim to 10)
        messages = trim_context(messages, max_messages=10)
        # Format conversation as prompt
        conversation = ""
        for msg in messages:
            role = "User" if msg.author == "user" else "Assistant"
            conversation += f"{role}: {msg.content}\n\n"

        # Use build_run_instructions as the task
        task = build_run_instructions(conversation)

        # Run the agent
        agent_trace = agent.run(task, max_turns=30)

        # Display tool usage information
        if hasattr(agent_trace, "spans"):
            for span in agent_trace.spans:
                tool_msg = cl.Message(
                    content=f"⚙️ Used: **{span.name}**",
                    author="Agent Steps",
                )
                await tool_msg.send()
                tool_msg.author = "assistant"
                messages.append(tool_msg)

        # Send the final response
        if agent_trace.final_output:
            # json_output = json.loads(agent_trace.final_output)
            # output_to_render = json_output.get("agent_code") # + "\n\n" + json_output.get("run_instructions") + "\n\n" + json_output.get("dependencies") # noqa: E501
            output_to_render = agent_trace.final_output
            response_msg = cl.Message(content=output_to_render)
            response_msg.author = "assistant"
            await response_msg.send()
            messages.append(response_msg)

        cl.user_session.set("messages", messages)

    except Exception as e:
        error_msg = cl.Message(content=f"Error: {str(e)}")
        error_msg.author = "assistant"
        await error_msg.send()


if __name__ == "__main__":
    from chainlit.cli import run_chainlit

    run_chainlit(__file__)
