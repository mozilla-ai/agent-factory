from any_agent.config import MCPStdio


def no_docker_mcp(MCPStdio_tool_config: MCPStdio, prompt_id: str):
    """Makes sure that MCPStdio tool is not running on docker."""
    assert "docker" not in MCPStdio_tool_config.command.lower(), f"Docker MCP cannot be used in {prompt_id}"
