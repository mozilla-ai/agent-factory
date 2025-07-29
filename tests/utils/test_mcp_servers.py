import json
import os
import tempfile
from pathlib import Path

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def load_mcp_servers():
    """Load MCP servers from JSON file."""
    json_path = Path("docs/mcp-servers.json")
    with json_path.open() as f:
        data = json.load(f)
    return data["mcpServers"]


def pytest_generate_tests(metafunc):
    """Generate test parameters from MCP servers JSON."""
    if "server_name" in metafunc.fixturenames:
        servers = load_mcp_servers()
        metafunc.parametrize("server_name", list(servers.keys()))


@pytest.mark.asyncio
async def test_list_tools(server_name):
    """Test list_tools for each MCP server."""
    servers = load_mcp_servers()
    server_config = servers[server_name]

    # Skip if missing required env vars
    for env_var, placeholder in server_config.get("env", {}).items():
        if placeholder.startswith("YOUR_") and not os.environ.get(env_var):
            pytest.skip(f"Missing {env_var}")

    # Handle filesystem server with temp directory
    if server_name == "filesystem":
        with tempfile.TemporaryDirectory() as temp_dir:
            args = [temp_dir, temp_dir]
    else:
        args = server_config.get("args", [])

    # Skip obsidian (needs real vault)
    if server_name == "mcp-obsidian":
        pytest.skip("Needs real Obsidian vault path")

    server_params = StdioServerParameters(command=server_config["command"], args=args, env=server_config.get("env", {}))

    async with stdio_client(server_params) as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()
            result = await session.list_tools()
            assert result is not None
            assert hasattr(result, "tools")
