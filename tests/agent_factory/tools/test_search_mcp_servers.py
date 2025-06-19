import pytest

from agent_factory.tools import KEYS_TO_DROP, search_mcp_servers


@pytest.mark.parametrize("is_official", [True, False])
def test_search_mcp_servers_cleaned(is_official):
    results = search_mcp_servers("database", is_official=is_official)
    for result in results:
        assert all(k not in KEYS_TO_DROP for k in result)
        assert all("inputSchema" not in tool for tool in result.get("tools", []))
