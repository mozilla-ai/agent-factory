import shutil
import uuid
from pathlib import Path
from typing import Any

from agent_factory.utils.io_utils import BINARY_NAME_MCPD, run_binary

KEYS_TO_DROP = ("display_name", "repository", "homepage", "author", "categories", "tags", "examples")

# Define the base directory where all temporary directories will be created.
# This acts as the secure sandbox for the agent.
BASE_TEMP_CONFIG_DIR = Path("/tmp/mcpd").resolve()


def _cleanup_mcp_server_info(server_info):
    for k in KEYS_TO_DROP:
        server_info.pop(k, None)

    for tool in server_info.get("tools", []):
        tool.pop("inputSchema", None)

    return server_info


def search_mcp_servers(
    keyphrase: str,
    license: str | None = None,
    categories: list[str] | None = None,
    tags: list[str] | None = None,
    is_official: bool = False,
) -> list[dict[str, Any]]:
    """Search for MCP servers using a keyphrase and optional filters.

    This function queries the MCP server registry and returns servers matching the provided keyphrase.
    The keyphrase may appear in the server name or description. If set to "*", all servers are returned.

    Optional filters include `license`, `categories`, `tags`, and an `is_official` flag, which narrow results by:
    - license name (partial match),
    - declared categories (all supplied substrings must match),
    - declared tags (all supplied substrings must match),
    - whether the server is marked as official.

    If no servers match, an empty list is returned.

    Example:
    ```python
    search_mcp_servers(keyphrase="google calendar")
    search_mcp_servers(keyphrase="github", is_official=True)
    search_mcp_servers(keyphrase="github", license="MIT")
    search_mcp_servers(keyphrase="github", categories=["Dev Tools"])
    search_mcp_servers(keyphrase="mcp", tags=["automation", "llm"])
    ```

    Args:
        keyphrase: A string to search for in the MCP server registry.
                Must be a single keyphrase consisting of one or more words separated by spaces (no commas).
                When "*" acts as a wildcard returning all search results.
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


def initialize_mcp_config(config_path: Path) -> bool:
    """Initialize the config file used by mcpd.

    Example:
        ```python
        success = initialize_mcp_config(config_path=Path("/tmp/.mcpd.toml"))
        print("Config initialized successfully")
        ```

    Args:
        config_path: Path to the configuration file that should be created.

    Returns:
        bool: True if initialization succeeded.

    Raises:
        RuntimeError: If initialization fails (e.g., non-zero exit code).
    """
    args = ["init", f"--config-file={config_path}"]
    run_binary(BINARY_NAME_MCPD, args, ignore_response=True)
    return True


def register_mcp_server(
    config_path: Path,
    name: str,
    version: str | None = None,
    tools: list[str] | None = None,
) -> bool:
    """Register an MCP server that will be required by the generated agent.

    This function registers an MCP server using its `name` and `version`, writing to a declarative configuration file.
    If only a subset of the available tools for the server are required, they can be specified via the `tools` argument.
    If tools are not specified then 'all' the currently available tools will be allowed.

    Example:
        ```python
        success = register_mcp_server(
            Path("/tmp/.mcpd.toml"), "github", tools=["get_pull_request_status", "push_files"]
        )
        print("Server registered successfully")

        register_mcp_server(Path("/tmp/.mcpd.toml"), "github", version="v1.2.3")

        register_mcp_server(
            Path("/tmp/.mcpd.toml"),
            "github",
            version="v4.5.6",
            tools=["get_pull_request_status", "update_pull_request_branch"],
        )
        ```

    Args:
        config_path: Path to the initialized configuration file.
        name: A string which is the ID/name of the MCP server to be registered.
        version: Optional version to pin for this MCP server (if known).
        tools: Optional list (subset) of allowed tools to pin for this server. If none are supplied then all currently
            available tools are pinned.

    Returns:
        bool: True if server registration succeeded.

    Raises:
         RuntimeError: If server registration fails (e.g., non-zero exit code).
    """
    args = ["add", name, f"--config-file={config_path}"]

    if version is not None:
        args.extend(["--version", version])

    if tools:
        for tool in tools:
            args.extend(["--tool", tool])

    run_binary(BINARY_NAME_MCPD, args, ignore_response=True)
    return True


def create_temp_config_dir() -> tuple[Path, uuid.UUID, str]:
    """Creates a new, unique temporary directory inside the constrained base
    directory and returns its full path, UUID and a deletion key.

    The directory is persistent until explicitly deleted by `cleanup_temp_config_dir`.
    A secure key is stored inside the directory for deletion verification.

    Returns:
        Tuple containing:
            1. Path that should be used for configuration file creation,
                and that is read when using `read_temp_config_file`
            2. UUID identifier for the directory.
            3. Deletion key (required to delete the directory).

    Raises:
        RuntimeError: If `create_temp_dir` fails to create the directory and associated data.

    Example:
        ```python
        temp_dir, temp_dir_id, temp_dir_deletion_key = create_temp_dir()
        ```
    """
    try:
        # Ensure the base directory exists.
        BASE_TEMP_CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        # Create a unique directory name using a UUID.
        dir_uuid = uuid.uuid4()
        new_dir_path = BASE_TEMP_CONFIG_DIR / str(dir_uuid)
        new_dir_path.mkdir(parents=True, exist_ok=True)

        # Generate a unique key and store it in a file inside the new directory.
        deletion_key = str(uuid.uuid4())
        key_file_path = new_dir_path / "_key.txt"
        with Path.open(key_file_path, "w", encoding="utf-8") as f:
            f.write(deletion_key)

        return new_dir_path / ".mcpd.toml", dir_uuid, deletion_key

    except (FileNotFoundError, OSError) as e:
        raise RuntimeError("Cannot create temp config dir") from e

    except Exception as e:
        raise RuntimeError("Unknown error creating temp config dir") from e


def read_temp_config_file(dir_uuid: uuid.UUID) -> str:
    """Reads the '.mcpd.toml' file from the temporary directory identified by its UUID.
    This function is narrowly scoped and includes a security check to prevent path traversal.

    Args:
        dir_uuid: The UUID of the temporary directory.

    Returns:
        The content of the file as a string.

    Raises:
        RuntimeError: If the file does not exist, or the UUID is not a valid identifier for the temporary directory.
    """
    file_name = ".mcpd.toml"

    # Build the path to the directory and the requested file.
    target_dir = BASE_TEMP_CONFIG_DIR / str(dir_uuid)
    if not target_dir.is_dir():
        raise RuntimeError(f"Temp config directory doesn't exist: {dir_uuid}")

    requested_file_path = target_dir / file_name
    if not requested_file_path.is_file():
        raise RuntimeError(f"Temp config file doesn't exist: {requested_file_path}")

    # Ensure the requested path is inside the base path.
    resolved_base_path = BASE_TEMP_CONFIG_DIR.resolve()
    resolved_requested_path = requested_file_path.resolve(strict=True)
    if resolved_requested_path.is_relative_to(resolved_base_path):
        with Path.open(resolved_requested_path, encoding="utf-8") as f:
            return f.read()
    else:
        raise RuntimeError(f"Attempted to read file outside of allowed directory: {resolved_requested_path}")


def cleanup_temp_config_dir(dir_uuid: uuid.UUID, deletion_key: str) -> bool:
    """Deletes a temporary directory and all its contents, identified by its UUID.

    Includes a security check to prevent deleting other (non-temporary) directories
    and a key verification check to ensure ownership.

    Args:
        dir_uuid: UUID of the temporary directory to delete.
        deletion_key: The secret key required to authorize the deletion.

    Returns:
        bool: True if directory was successfully deleted, False if deletion key was incorrect.

    Raises:
        RuntimeError: If the directory is not found, outside allowed directory, or other errors occur.
    """
    target_dir = BASE_TEMP_CONFIG_DIR / str(dir_uuid)
    key_file_path = target_dir / "_key.txt"

    # Ensure the requested path is inside the base path.
    resolved_base_path = BASE_TEMP_CONFIG_DIR.resolve()
    resolved_target_path = target_dir.resolve()
    if not resolved_target_path.is_relative_to(resolved_base_path):
        raise RuntimeError(f"Attempted to delete directory outside of allowed directory: {resolved_target_path}")

    if not resolved_target_path.is_dir() or not key_file_path.exists():
        raise RuntimeError(f"Directory with UUID '{dir_uuid}' not found or key file is missing.")

    with Path.open(key_file_path, encoding="utf-8") as f:
        stored_key = f.read().strip()

    if stored_key == deletion_key:
        shutil.rmtree(resolved_target_path)
        return True
    else:
        return False
