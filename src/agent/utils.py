import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger
from mcpm.utils.repository import RepositoryManager
from templates import AGENT_CODE_TEMPLATE

DEFAULT_REGISTRY_URL = "https://getmcp.io/api/servers.json"

KEYS_TO_DROP = ("display_name", "repository", "homepage", "author", "categories", "tags", "docker_url", "examples")


def _cleanup_mcp_server_info(server_info):
    for k in KEYS_TO_DROP:
        server_info.pop(k, None)

    for tool in server_info.get("tools", []):
        tool.pop("inputSchema")

    return server_info


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
        A list of server descriptions that match the search criteria.
        If no servers match, returns an empty list.
        Returns official servers if `is_official` is set to `True`.
    """
    repository_manager = RepositoryManager(repo_url=DEFAULT_REGISTRY_URL)
    servers = repository_manager.search_servers(keyword)

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


def _prepare_output_dir() -> Path:
    output_dir = Path.cwd()
    uid = datetime.now().strftime("%Y-%m-%d_%H:%M:%S") + "_" + str(uuid.uuid4())[:8]
    output_dir = output_dir / "generated_workflows" / uid
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def save_agent_outputs(result: dict[str, str]) -> None:
    """Save the agent outputs to files.

    This function takes a dictionary containing the agent outputs and saves them to
    an output directory. It creates three different files in the output directory:
        - agent.py: Contains the agent code.
        - INSTRUCTIONS.md: Contains the run instructions in Markdown format.
        - requirements.txt: Contains the dependencies line by line.

    Args:
        result: A dictionary containing the agent outputs. It should include the following keys:
            - agent_code: The Python code for the agent.
            - run_instructions: The instructions for running the agent in Markdown format.
            - dependencies: A string containing the dependencies required by the agent, one per line.

    Raises:
        Exception: If there is an error while writing the files to the output directory.
    """
    output_dir = _prepare_output_dir()
    try:
        agent_path = output_dir / "agent.py"
        instructions_path = output_dir / "INSTRUCTIONS.md"
        requirements_path = output_dir / "requirements.txt"
        agent_code = AGENT_CODE_TEMPLATE.format(**result)

        with agent_path.open("w", encoding="utf-8") as f:
            f.write(agent_code)

        with instructions_path.open("w", encoding="utf-8") as f:
            f.write(result["run_instructions"])

        with requirements_path.open("w", encoding="utf-8") as f:
            f.write(result["dependencies"])

        logger.info(f"Agent files saved to {output_dir}")

    except Exception as e:
        print(f"Warning: Failed to parse and save agent outputs: {str(e)}")
