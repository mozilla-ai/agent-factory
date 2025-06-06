import logging

from mcpm.utils.repository import RepositoryManager

logger = logging.getLogger(__name__)

DEFAULT_REGISTRY_URL = "https://mcpm.sh/api/servers.json"


def search_mcp_servers(keyword: str) -> list[str]:
    """Search for available MCP servers based on a single keyword.

    This function queries the MCP server registry and filters the results
    based on the provided keyword.
    The keyword can be a part of the server name, description, or tags.
    It returns a list of matching servers.

    Example:
    ```python
    search_mcp_server("github")
    ```

    Args:
        keyword: A string to search for in the MCP server registry.

    Returns:
        A list of server names that match the search criteria.
        If no servers are found, an empty list is returned.
    """
    repository_manager = RepositoryManager(repo_url=DEFAULT_REGISTRY_URL)
    servers = repository_manager.search_servers(keyword)

    return servers
