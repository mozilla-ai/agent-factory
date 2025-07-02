from unittest.mock import Mock, patch

import pytest

from agent_factory.tools import KEYS_TO_DROP, search_mcp_servers


@pytest.mark.parametrize("is_official", [True, False])
def test_search_mcp_servers_cleaned(is_official):
    """Test that search_mcp_servers returns cleaned server descriptions."""
    results = search_mcp_servers("database", is_official=is_official)
    for result in results:
        assert all(k not in KEYS_TO_DROP for k in result)
        assert all("inputSchema" not in tool for tool in result.get("tools", []))


@pytest.mark.parametrize("keyword", ["slack", "github", "google calendar"])
def test_search_mcp_servers_contains_keyword(keyword):
    """Test that search results contain the keyword in name, description, or tags."""
    results = search_mcp_servers(keyword)

    for result in results:
        keyword_found = (
            (keyword.lower() in result.get("name", "").lower())
            or (keyword.lower() in result.get("description", "").lower())
            or any(keyword.lower() in tag.lower() for tag in result.get("tags", []))
        )
        assert keyword_found, f"Keyword '{keyword}' not found in result: {result}"


@pytest.mark.parametrize("invalid_keyword", ["slack,github", ""])
def test_search_mcp_servers_validate_single_word(invalid_keyword):
    """Test that search_mcp_servers raises ValueError for multi-word or empty keywords."""
    with pytest.raises(ValueError, match="Keyword must be a single word"):
        search_mcp_servers(invalid_keyword)


def test_search_mcp_servers_normalizes_keyword():
    """Test that search_mcp_servers applies strip() and lower() to the keyword."""
    mock_repo = Mock()
    mock_repo.search_servers.return_value = []

    test_cases = [
        ("  GITHUB  ", "github"),
        ("GitHub", "github"),
    ]

    for input_kw, expected_kw in test_cases:
        with patch("agent_factory.tools.RepositoryManager", return_value=mock_repo):
            search_mcp_servers(input_kw)
            mock_repo.search_servers.assert_called_with(expected_kw)
            mock_repo.reset_mock()
