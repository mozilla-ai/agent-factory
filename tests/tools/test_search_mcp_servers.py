from unittest.mock import Mock, patch

import pytest

from agent_factory.factory_tools import KEYS_TO_DROP, search_mcp_servers


@pytest.mark.parametrize("is_official", [True, False])
def test_search_mcp_servers_cleaned(is_official):
    """Test that search_mcp_servers returns cleaned server descriptions."""
    results = search_mcp_servers("database", is_official=is_official)
    for result in results:
        assert all(k not in KEYS_TO_DROP for k in result)
        assert all("inputSchema" not in tool for tool in result.get("tools", []))


@pytest.mark.parametrize("keyphrase", ["slack", "github", "google calendar"])
def test_search_mcp_servers_contains_keyphrase(keyphrase):
    """Test that search results contain the keyphrase in name, description, or tags."""
    results = search_mcp_servers(keyphrase)

    for result in results:
        keyphrase_found = (
            (keyphrase.lower() in result.get("name", "").lower())
            or (keyphrase.lower() in result.get("description", "").lower())
            or any(keyphrase.lower() in tag.lower() for tag in result.get("tags", []))
        )
        assert keyphrase_found, f"Keyphrase '{keyphrase}' not found in result: {result}"


@pytest.mark.parametrize("invalid_keyphrase", ["slack,github", ""])
def test_search_mcp_servers_validate_single_word(invalid_keyphrase):
    """Test that search_mcp_servers raises ValueError for multi-word or empty keyphrases."""
    with pytest.raises(ValueError, match="Keyphrase must be a single word"):
        search_mcp_servers(invalid_keyphrase)


def test_search_mcp_servers_normalizes_keyphrase():
    """Test that search_mcp_servers applies strip() and lower() to the keyphrase."""
    mock_repo = Mock()
    mock_repo.search_servers.return_value = []

    test_cases = [
        ("  GITHUB  ", "github"),
        ("GitHub", "github"),
    ]

    for input_kw, expected_kw in test_cases:
        with patch("agent_factory.factory_tools.RepositoryManager", return_value=mock_repo):
            search_mcp_servers(input_kw)
            mock_repo.search_servers.assert_called_with(expected_kw)
            mock_repo.reset_mock()
