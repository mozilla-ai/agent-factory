import os

import chainlit as cl
import openai
from agents import Agent, Runner
from agents.mcp import MCPServerSse, MCPServerStdio
from dotenv import load_dotenv

load_dotenv()

# Set OpenAI API key
openai.api_key = os.environ["OPENAI_API_KEY"]

MCP_TOOLS = []
messages = []

# Create GitHub agent using OpenAI Agents SDK
github_agent = Agent(
    name="GitHub Agent",
    instructions="You are able to handle issues and requests on a GitHub repository. You can use your tools to help with the task.",  # noqa: E501
    model="gpt-4.1",
)


def format_messages(all_cl_messages: list[cl.Message]):
    """Convert Chainlit messages to OpenAI format"""
    if not all_cl_messages:
        return []

    # Get the latest message content for the task
    current_message = all_cl_messages[-1]
    return current_message.content


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
        messages.append(message)
        cl.user_session.set("messages", messages)

        # Prepare MCP servers for OpenAI Agents SDK
        mcp_servers = []

        # Register existing MCP tools
        if MCP_TOOLS:
            for tool in MCP_TOOLS:
                if tool.clientType == "sse":
                    mcp_server = MCPServerSse({"url": tool.url, "timeout": 100})
                    await mcp_server.connect()
                    mcp_servers.append(mcp_server)
                elif tool.clientType == "stdio":
                    mcp_server = MCPServerStdio(
                        {"command": tool.command, "args": tool.args, "env": getattr(tool, "env", None)}
                    )
                    await mcp_server.connect()
                    mcp_servers.append(mcp_server)

        # Add GitHub MCP server
        github_mcp_server = MCPServerStdio(
            {
                "command": "docker",
                "args": ["run", "-i", "--rm", "-e", "GITHUB_PERSONAL_ACCESS_TOKEN", "ghcr.io/github/github-mcp-server"],
                "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": os.environ["GITHUB_PERSONAL_ACCESS_TOKEN"]},
            }
        )
        await github_mcp_server.connect()
        mcp_servers.append(github_mcp_server)

        # Update agent with MCP servers
        github_agent.mcp_servers = mcp_servers

        # Format the input task
        task = format_messages(messages)

        # Run the agent with the task
        result = await Runner.run(github_agent, task)

        # Display tool usage information
        if hasattr(result, "steps"):
            for step in result.steps:
                if hasattr(step, "tool_calls"):
                    for tool_call in step.tool_calls:
                        tool_msg = cl.Message(
                            content=f"⚙️ Used tool: **{tool_call.function.name}**\nArguments: `{tool_call.function.arguments}`",  # noqa: E501
                            author="Agent Steps",
                        )
                        await tool_msg.send()
                        messages.append(tool_msg)

        # Send the final response
        if result.final_output:
            response_msg = cl.Message(content=result.final_output)
            await response_msg.send()
            messages.append(response_msg)

        cl.user_session.set("messages", messages)

        # Cleanup MCP connections
        for server in mcp_servers:
            await server.cleanup()

    except Exception as e:
        error_msg = cl.Message(content=f"Error: {str(e)}")
        await error_msg.send()


if __name__ == "__main__":
    from chainlit.cli import run_chainlit

    run_chainlit(__file__)
