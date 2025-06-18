from agent_factory.tools import KEYS_TO_DROP, search_mcp_servers


def test_search_mcp_servers_cleaned():
    results = search_mcp_servers("tts")
    for result in results:
        assert all(k not in KEYS_TO_DROP for k in result)
        assert all("inputSchema" not in tool for tool in result.get("tools", []))
