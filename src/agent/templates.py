TOOLS_REMINDER = """Use appropriate tools in the agent configuration:
- Select relevant tools from `tools/README.md`.
- Use the `search_mcp_servers` tool to discover and add MCP servers that provide relevant tools
    to the configuration.

Always use the simplest and most efficient tools available for the task.
"""


USER_PROMPT = """Generate Python code for an agentic workflow using the `any-agent` library
to do the following:
{0}

{1}
"""
