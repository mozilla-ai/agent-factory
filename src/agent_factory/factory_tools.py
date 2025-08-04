from pathlib import Path
from typing import Any

from agent_factory.utils.io_utils import BINARY_NAME_MCPD, run_binary

KEYS_TO_DROP = ("display_name", "repository", "homepage", "author", "categories", "tags", "examples")


def _cleanup_mcp_server_info(server_info):
    for k in KEYS_TO_DROP:
        server_info.pop(k, None)

    for tool in server_info.get("tools", []):
        tool.pop("inputSchema")

    return server_info


def search_mcp_servers(
    keyphrase: str,
    license: str | None = None,
    categories: list[str] | None = None,
    tags: list[str] | None = None,
    is_official: bool = False,
) -> list[dict[str, Any]]:
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
        license: Optional string which describes a full or partial match of the license for any MCP server.
                e.g. Apache, MIT.
        categories: Optional list of one or more strings to use to filter by categories the MCP server has declared to
                the registry.
                When multiple values are supplied matching is cumulative requiring partial (sub-string) matches for all
                categories.
        tags: Optional list of one or more strings to use to filter by tags the MCP server has declared to the registry.
                When multiple values are supplied matching is cumulative requiring partial (sub-string) matches for all
                tags.
        is_official: If `True`, only official servers will be returned. Defaults to `False`.

    Returns:
        A list of server descriptions that match the search criteria.
        If no servers match, returns an empty list.
        Returns official servers if `is_official` is set to `True`.

    Raises:
        ValueError: If keyphrase contains commas, indicating multiple words.
        ValueError: If the search results are not valid JSON.
        RuntimeError: If there are issues executing the search.
    """
    if not keyphrase.strip() or any(sep in keyphrase for sep in [","]):
        raise ValueError("Keyphrase must be a single word (no commas)")

    # Normalize and sanitize.
    keyphrase = keyphrase.strip().lower()

    args = ["search", keyphrase, "--format=json"]
    if categories:
        for category in categories:
            args.extend(["--category", category])

    if tags:
        for tag in tags:
            args.extend(["--tag", tag])

    if license:
        args.extend(["--license", license])

    if is_official:
        args.extend(["--official"])

    output = run_binary(BINARY_NAME_MCPD, args)
    if output.get("results") is None or not output.get("results"):
        return []

    servers = output.get("results")

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
