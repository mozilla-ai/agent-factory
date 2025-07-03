from pathlib import Path
from typing import Any

from mcpm.utils.repository import RepositoryManager

DEFAULT_REGISTRY_URL = "https://getmcp.io/api/servers.json"

KEYS_TO_DROP = ("display_name", "repository", "homepage", "author", "categories", "tags", "docker_url", "examples")


def _cleanup_mcp_server_info(server_info):
    for k in KEYS_TO_DROP:
        server_info.pop(k, None)

    for tool in server_info.get("tools", []):
        tool.pop("inputSchema")

    return server_info


def search_mcp_servers(keyphrase: str, is_official: bool = False) -> list[dict[str, Any]]:
    """Search for available MCP servers based on a single keyphrase (one or more words separated by spaces).

    This function queries the MCP server registry and filters the results based on the provided
    keyphrase. The keyphrase can be a part of the server name, description, or tags.

    It returns a list of matching servers, and if no servers match the criteria, it returns an empty
    list.

    Example:
    ```python
    search_mcp_servers(keyphrase="github", is_official=True)
    search_mcp_servers(keyphrase="google calendar")
    ```

    Args:
        keyphrase: A string to search for in the MCP server registry.
                 Must be a single keyphrase consisting of one or more words separated by spaces (no commas).
        is_official: If `True`, only official servers will be returned. Defaults to `False`.

    Returns:
        A list of server descriptions that match the search criteria.
        If no servers match, returns an empty list.
        Returns official servers if `is_official` is set to `True`.

    Raises:
        ValueError: If keyphrase contains commas, indicating multiple words.
    """
    if not keyphrase.strip() or any(sep in keyphrase for sep in [","]):
        raise ValueError("Keyphrase must be a single word (no commas)")

    repository_manager = RepositoryManager(repo_url=DEFAULT_REGISTRY_URL)
    servers = repository_manager.search_servers(keyphrase.strip().lower())

    if is_official:
        servers = filter(lambda server: server.get("is_official", False), servers)

    return [_cleanup_mcp_server_info(server) for server in servers]


def read_file(file_name: str) -> str:
    """Read the contents of the given `file_name`.

    Args:
        file_name: The path to the file you want to read.

    Returns:
        The contents of `file_name`.

    Raises:
        ValueError: For the following cases:
            - If the path to the file is not allowed.
    """
    file_path = Path(file_name)

    # TODO: this is just a hacky way to restrict file access to
    # "mimic" the MCP filesystem server.
    if file_path.parent.name != "tools":
        raise ValueError(f"`file_name` parent dir must be `tools`. Got {file_path.parent}")

    return file_path.read_text()
