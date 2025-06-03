import os

import chainlit as cl
from any_agent import AgentConfig, AgentFramework, AnyAgent
from any_agent.config import MCPStdio
from dotenv import load_dotenv

load_dotenv()

MCP_TOOLS = []
messages = []

# Create GitHub agent using any_agent
framework = AgentFramework.OPENAI
github_agent = AnyAgent.create(
    framework,
    AgentConfig(
        model_id="gpt-4.1",
        instructions="You are able to handle issues and requests on a GitHub repository. You can use your tools to help with the task.",  # noqa: E501
    ),
)


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

        # Configure tools for any_agent
        tools = []

        # Register existing MCP tools
        if MCP_TOOLS:
            for tool in MCP_TOOLS:
                if tool.clientType == "stdio":
                    mcp_tool = MCPStdio(command=tool.command, args=tool.args, env=getattr(tool, "env", None))
                    tools.append(mcp_tool)

        # Add GitHub MCP server
        github_mcp_tool = MCPStdio(
            command="docker",
            args=["run", "-i", "--rm", "-e", "GITHUB_PERSONAL_ACCESS_TOKEN", "ghcr.io/github/github-mcp-server"],
            env={"GITHUB_PERSONAL_ACCESS_TOKEN": os.environ["GITHUB_PERSONAL_ACCESS_TOKEN"]},
        )
        tools.append(github_mcp_tool)

        # Update agent config with tools
        github_agent.config.tools = tools

        # Trim context to the last 10 messages
        messages = trim_context(messages, max_messages=10)
        # Format the conversation history into a prompt
        conversation = ""
        for msg in messages:
            role = "User" if msg.author == "user" else "Assistant"
            conversation += f"{role}: {msg.content}\n\n"

        # Prepare the task for the agent
        task = f"Here is the conversation history:\n\n{conversation}\nPlease respond to the latest message."

        # Run the agent with the conversation history
        agent_trace = github_agent.run(task, max_turns=30)

        # Display tool usage information
        if hasattr(agent_trace, "spans"):
            for span in agent_trace.spans:
                if hasattr(span, "tool_calls") and span.tool_calls:
                    for tool_call in span.tool_calls:
                        tool_msg = cl.Message(
                            content=f"⚙️ Used tool: **{tool_call.name}**\nArguments: `{tool_call.input}`",  # noqa: E501
                            author="Agent Steps",
                        )
                        await tool_msg.send()
                        tool_msg.author = "assistant"
                        messages.append(tool_msg)

        # Send the final response
        if agent_trace.final_output:
            response_msg = cl.Message(content=agent_trace.final_output)
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
