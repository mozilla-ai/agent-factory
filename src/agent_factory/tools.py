import logging
from typing import Any

from mcpm.utils.repository import RepositoryManager

logger = logging.getLogger(__name__)

DEFAULT_REGISTRY_URL = "https://mcpm.sh/api/servers.json"


def search_mcp_servers(keyword: str, is_official: bool = False) -> list[dict[str, Any]]:
    """Search for available MCP servers based on a single keyword.

    This function queries the MCP server registry and filters the results based on the provided
    keyword. The keyword can be a part of the server name, description, or tags.

    It returns a list of matching servers, and if no servers match the criteria, it returns an empty
    list.

    Example:
    ```python
    search_mcp_servers(keyword="github", is_official=True)
    ```

    Args:
        keyword: A string to search for in the MCP server registry.
        is_official: If `True`, only official servers will be returned. Defaults to `False`.

    Returns:
        A list of server names that match the search criteria. If no servers match, returns an empty
        list. Returns official servers if `is_official` is set to `True`.
    """
    repository_manager = RepositoryManager(repo_url=DEFAULT_REGISTRY_URL)
    servers = repository_manager.search_servers(keyword)

    if is_official:
        official_servers = filter(lambda server: server.get("is_official", False), servers)
        return list(official_servers)

    return servers
