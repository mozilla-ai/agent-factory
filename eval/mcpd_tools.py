"""Custom tools for integrating with mcpd's REST API.

This module provides a bridge between any-agent and mcpd's REST API.
Since mcpd doesn't support the WebSocket-based streamable-http protocol,
we implement direct REST API calls instead.

Architecture:
- mcpd exposes REST endpoints at /api/v1/servers/{server}/tools/{tool}
- Tools are created as async functions compatible with any-agent
- Schema discovery is supported but falls back gracefully

Future AGNTCY Support:
- The mcpd_call_tool function accepts optional headers for DID auth
- When AGNTCY is merged, uncomment the header injection code
- No other changes needed - the architecture is future-proof
"""

import httpx
from typing import Any, Optional, Dict
import os


async def mcpd_call_tool(
    server: str, 
    tool: str, 
    args: dict[str, Any], 
    mcpd_url: str = "http://localhost:8090",
    headers: Optional[Dict[str, str]] = None
) -> str:
    """Call an MCP tool via mcpd's REST API.
    
    Args:
        server: MCP server name
        tool: Tool name to call
        args: Arguments for the tool
        mcpd_url: Base URL for mcpd
        headers: Optional headers (for future AGNTCY DID auth)
    """
    try:
        # Future: AGNTCY headers would be added here
        # headers = headers or {}
        # if agntcy_did := os.getenv("AGNTCY_DID"):
        #     headers["X-AGNTCY-DID"] = agntcy_did
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{mcpd_url}/api/v1/servers/{server}/tools/{tool}",
                json=args,
                headers=headers,
                timeout=30.0,
            )
            response.raise_for_status()
            result = response.json()
            
            # mcpd returns the extracted message in the "body" field
            if isinstance(result, dict) and "body" in result:
                return result["body"]
            # Fallback for direct string responses
            return str(result)
    except Exception as e:
        return f"Error calling MCP tool {tool}: {e!s}"


async def get_server_tools(server: str, mcpd_url: str = "http://localhost:8090") -> list[dict]:
    """Fetch available tools from mcpd server."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{mcpd_url}/api/v1/servers/{server}/tools",
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("tools", [])
    except Exception:
        # Fallback to empty list if tools endpoint fails
        return []


def create_mcpd_tool(
    server: str, 
    tool_name: str, 
    mcpd_url: str = "http://localhost:8090",
    tool_schema: Optional[dict] = None
):
    """Create a tool function that calls mcpd.
    
    Args:
        server: MCP server name
        tool_name: Name of the tool
        mcpd_url: Base URL for mcpd
        tool_schema: Optional tool schema from mcpd (for future use)
    """
    # Extract description and parameters from schema if available
    description = f"Call {tool_name} via mcpd server {server}"
    annotations = {"return": str}
    
    if tool_schema:
        description = tool_schema.get("description", description)
        # Parse inputSchema to add parameter annotations
        if input_schema := tool_schema.get("inputSchema"):
            properties = input_schema.get("properties", {})
            required = input_schema.get("required", [])
            for param_name, param_info in properties.items():
                # Simple type mapping - could be enhanced
                param_type = str
                if param_info.get("type") == "integer":
                    param_type = int
                elif param_info.get("type") == "number":
                    param_type = float
                elif param_info.get("type") == "boolean":
                    param_type = bool
                
                # Use Optional for non-required params
                if param_name not in required:
                    from typing import Optional
                    annotations[param_name] = Optional[param_type]
                else:
                    annotations[param_name] = param_type
    
    async def tool_func(**kwargs) -> str:
        return await mcpd_call_tool(server, tool_name, kwargs, mcpd_url)
    
    tool_func.__name__ = tool_name
    tool_func.__doc__ = description
    tool_func.__annotations__ = annotations
    
    return tool_func


# Pre-configured tools for filesystem operations  
def create_filesystem_tools(mcpd_url: str = "http://localhost:8090"):
    """Create filesystem tools that work with mcpd.
    
    Note: Currently uses static tool definitions. Future versions
    will dynamically fetch tool schemas from mcpd.
    """
    # Static definitions for now - future versions would fetch from mcpd
    filesystem_tools = [
        {
            "name": "read_file",
            "description": "Read the contents of a file at the specified path",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file"}
                },
                "required": ["path"]
            }
        },
        {
            "name": "list_directory", 
            "description": "List the contents of a directory at the specified path",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the directory"}
                },
                "required": ["path"]
            }
        }
    ]
    
    tools = []
    for tool_def in filesystem_tools:
        tool = create_mcpd_tool("filesystem", tool_def["name"], mcpd_url, tool_def)
        # Add parameter annotations based on schema
        if input_schema := tool_def.get("inputSchema", {}).get("properties", {}):
            for param_name in input_schema:
                tool.__annotations__[param_name] = str
        tools.append(tool)
    
    return tools


async def create_server_tools(
    server: str, 
    tool_names: Optional[list[str]] = None,
    mcpd_url: str = "http://localhost:8090"
):
    """Create tools for a specific mcpd server with dynamic discovery.
    
    Args:
        server: MCP server name
        tool_names: Optional list of specific tools to create. If None, creates all.
        mcpd_url: Base URL for mcpd
        
    Returns:
        List of callable tool functions
        
    Note: Falls back to basic tool creation if schema fetch fails.
    This ensures compatibility during the AGNTCY transition.
    """
    # Try to fetch tool schemas
    tool_schemas = await get_server_tools(server, mcpd_url)
    schema_map = {t["name"]: t for t in tool_schemas} if tool_schemas else {}
    
    # If specific tools requested
    if tool_names:
        tools = []
        for tool_name in tool_names:
            schema = schema_map.get(tool_name)
            tool = create_mcpd_tool(server, tool_name, mcpd_url, schema)
            # Add proper annotations even without schema
            if not schema and tool_name == "read_file":
                tool.__annotations__["path"] = str
            elif not schema and tool_name == "list_directory":
                tool.__annotations__["path"] = str
            tools.append(tool)
        return tools
    
    # Create all available tools
    if schema_map:
        return [
            create_mcpd_tool(server, schema["name"], mcpd_url, schema)
            for schema in tool_schemas
        ]
    
    # Fallback if no schemas available
    return []


async def create_all_server_tools(
    servers: list[dict[str, Any]],
    mcpd_url: str = "http://localhost:8090"
) -> list:
    """Create tools for multiple mcpd servers, mimicking McpdClient.agent_tools().
    
    This function provides a drop-in replacement for the mcpd Python client's
    agent_tools() method, allowing full migration from the PyPI mcpd package.
    
    Args:
        servers: List of server configs, each with 'name' and optional 'tools'
                 Example: [{"name": "filesystem", "tools": ["read_file"]}, {"name": "github"}]
        mcpd_url: Base URL for mcpd
        
    Returns:
        List of all callable tool functions from all servers
        
    Usage:
        # Replace this pattern from generated agents:
        mcpd_client = McpdClient(api_endpoint=MCPD_ENDPOINT)
        mcp_server_tools = mcpd_client.agent_tools()
        
        # With:
        mcp_servers = [{"name": "filesystem"}, {"name": "github", "tools": ["search_issues"]}]
        mcp_server_tools = await create_all_server_tools(mcp_servers, MCPD_ENDPOINT)
    """
    all_tools = []
    
    for server_config in servers:
        server_name = server_config.get("name")
        tool_names = server_config.get("tools")  # None means all tools
        
        if not server_name:
            continue
            
        try:
            tools = await create_server_tools(server_name, tool_names, mcpd_url)
            all_tools.extend(tools)
            print(f"Loaded {len(tools)} tools from server '{server_name}'")
        except Exception as e:
            print(f"Warning: Failed to load tools from server '{server_name}': {e}")
    
    return all_tools