import json
import subprocess
import tempfile
from contextlib import nullcontext
from pathlib import Path
from typing import Any

from agent_factory.utils.logging import logger

BINARY_NAME_MCPD = "mcpd"


def run_binary(path: str, args: list[str], ignore_response: bool = False) -> dict:
    """Run a compiled binary and parse its JSON output from STDOUT.

    Uses subprocess to execute the specified binary with arguments.
    Unless `ignore_response` is `True`, captures STDOUT, and attempts to decode it as JSON.

    Args:
        path: Path to the executable binary.
        args: List of arguments to pass to the binary.
        ignore_response: If `True`, STDOUT response is ignored and an empty response is returned.

    Returns:
        Parsed JSON output as a Python dictionary.

    Raises:
        RuntimeError: If the subprocess fails (e.g., non-zero exit code).
        ValueError: If the STDOUT response cannot be parsed as valid JSON when response is not being ignored.
    """
    try:
        result = subprocess.run([path, *args], capture_output=True, text=True, check=True)
        if ignore_response:
            logger.info(f"Ignoring binary ({path}) STDOUT response, return code: {result.returncode}")
            return {"return_code": result.returncode}
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        logger.error(f"Command '{e.cmd}' failed with code {e.returncode}")
        logger.error(f"Stderr: {e.stderr}")
        raise RuntimeError("Subprocess failed") from e
    except json.JSONDecodeError as e:
        logger.error("Failed to parse JSON from subprocess output")
        logger.error(f"Output was: {result.stdout.strip()}")
        raise ValueError("Invalid JSON output") from e
    except FileNotFoundError as e:
        logger.error(f"Binary not found at path: {path}")
        raise RuntimeError(f"Binary not found: {path}") from e
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise RuntimeError("An unexpected error occurred during binary execution") from e


def initialize_mcp_config(config_path: Path) -> int:
    """Initialize the config file used by mcpd.

    Example:
        ```python
        initialize_mcp_config(config_path=Path("/tmp/.mcpd.toml"))
        ```

    Args:
        config_path: Path to the configuration file that should be created.

    Raises:
        RuntimeError: If initialization fails (e.g., non-zero exit code).
    """
    args = ["init", f"--config-file={config_path}"]
    result = run_binary(BINARY_NAME_MCPD, args, ignore_response=True)

    try:
        return_code = int(result["return_code"])
    except KeyError as e:
        raise RuntimeError("Failed to initialize MCP config") from e

    if return_code != 0:
        raise RuntimeError("Failed to initialize MCP config")

    return return_code


def register_mcp_server(
    name: str, config_path: Path, version: str | None = None, tools: list[str] | None = None
) -> int:
    """Register an MCP server that will be required by the generated agent.

    This function registers an MCP server using its `name` and `version`, writing to a declarative configuration file.
    If only a subset of the available tools for the server are required, they can be specified via the `tools` argument.
    If tools are not specified then 'all' the currently available tools will be allowed.

    Example:
        ```python
        register_mcp_server(
            config_path=Path("/tmp/.mcpd.toml"), name="github", tools=["get_pull_request_status", "push_files"]
        )

        register_mcp_server(config_path=Path("/tmp/.mcpd.toml"), name="github", version="v1.2.3")

        register_mcp_server(
            config_path=Path("/tmp/.mcpd.toml"),
            name="github",
            version="v4.5.6",
            tools=["get_pull_request_status", "update_pull_request_branch"],
        )
        ```

    Args:
        name: A string which is the ID/name of the MCP server to be registered.
        version: Optional version to pin for this MCP server (if known).
        tools: Optional list (subset) of allowed tools to pin for this server. If none are supplied then all currently
            available tools are pinned.
        config_path: Path to the initialized configuration file.

    Raises:
         RuntimeError: If server registration fails (e.g., non-zero exit code).
    """
    args = ["add", name, f"--config-file={config_path}"]

    if version is not None:
        args.extend(["--version", version])

    if tools:
        for tool in tools:
            args.extend(["--tool", tool])

    result = run_binary(BINARY_NAME_MCPD, args, ignore_response=True)

    try:
        return_code = int(result["return_code"])
    except KeyError as e:
        raise RuntimeError("Failed to register MCP server") from e

    if return_code != 0:
        raise RuntimeError(f"Failed to register MCP server '{name}' with version '{version}' and tools '{tools}'")

    return return_code


def export_mcpd_config_artifacts(
    agent_factory_outputs: dict[str, Any], output_dir: Path | None = None
) -> dict[str, str]:
    """Export mcpd configuration files as sanitized artifacts.

    Initialize an mcpd config file (`.mcpd.toml`) in a temporary directory from the supplied Agent Factory outputs.
    Parse the contents of the config file to generate portable configuration files that separate the configuration
    structure from sensitive values, making the generated agent more portable while protecting secrets.

    The portable configuration files only handle required variables (not optional ones) for an MCP server.

    Args:
        agent_factory_outputs: The outputs from the Agent Factory which should contain a key named `mcp_servers`. The
            value should be a a list of dictionaries. Each dictionary should contain the name of the MCP server and the
            tools required by the generated agent.
        output_dir: Optional path to use as output directory for generated files. If None, a temporary directory will be
            created and automatically cleaned up. If provided, the directory and its contents will be preserved for
            further use (this causes a side effect).

    Returns:
        Dictionary with exported configuration artifacts.
        May contain:
            - ".mcpd.toml": The original mcpd configuration file content.
            - ".env": Environment contract with placeholders for required variables.
            - "secrets.prod.toml": Sanitized execution context safe for version control.
        Or an empty dictionary when the mcpd configuration doesn't exist in the supplied Agent Factory outputs.

    Note:
        If mcpd export fails, warnings are logged but the function continues.
        When `output_dir` is None, temporary files are cleaned up automatically.
        When `output_dir` is provided, all generated files remain in the specified directory (not recommended).
    """
    exported_artifacts = {}

    mcp_servers: list[dict[str, str | list[str]]] | None = agent_factory_outputs.get("mcp_servers")
    if not mcp_servers:
        logger.warning("Agent Factory output does not contain MCP servers, no related artifacts will be exported.")
        return exported_artifacts

    # Expected file names.
    config_file_name = ".mcpd.toml"
    contract_file_name = ".env"
    context_file_name = "secrets.prod.toml"

    # Use provided output_dir or create a temporary directory that will auto-cleanup.
    context = tempfile.TemporaryDirectory() if output_dir is None else nullcontext(output_dir)

    with context as working_dir:
        work_dir = Path(working_dir) if working_dir else output_dir

        mcpd_toml_path = work_dir / config_file_name  # type: ignore
        initialize_mcp_config(mcpd_toml_path)  # type: ignore

        for server in mcp_servers:
            register_mcp_server(server.get("name"), config_path=mcpd_toml_path, tools=server.get("tools"))  # type: ignore

        if mcpd_toml_path.exists():
            exported_artifacts[config_file_name] = mcpd_toml_path.read_text(encoding="utf-8")

        mcpd_contract_path = work_dir / contract_file_name  # type: ignore
        mcpd_context_path = work_dir / context_file_name  # type: ignore

        # Run 'mcpd config export' to generate artifacts.
        result = run_binary(
            BINARY_NAME_MCPD,
            [
                "config",
                "export",
                "--config-file",
                str(mcpd_toml_path),
                "--contract-output",
                str(mcpd_contract_path),
                "--context-output",
                str(mcpd_context_path),
            ],
            ignore_response=True,
        )

        try:
            return_code = int(result["return_code"])
            if return_code != 0:
                raise RuntimeError("Failed to export MCP config")
        except KeyError as e:
            raise RuntimeError("Failed to export MCP config") from e

        if mcpd_contract_path.exists():
            exported_artifacts[contract_file_name] = mcpd_contract_path.read_text(encoding="utf-8")

        if mcpd_context_path.exists():
            exported_artifacts[context_file_name] = mcpd_context_path.read_text(encoding="utf-8")

    return exported_artifacts
