import json
import subprocess
import tempfile
from contextlib import nullcontext
from pathlib import Path

from agent_factory.instructions import AGENT_CODE_TEMPLATE
from agent_factory.schemas import AgentParameters
from agent_factory.utils import clean_python_code_with_autoflake, validate_dependencies
from agent_factory.utils.logging import logger

TOOLS_DIR = Path(__file__).parent.parent / "tools"
BINARY_NAME_MCPD = "mcpd"


def export_mcpd_config_artifacts(
    agent_factory_outputs: dict[str, str], output_dir: Path | None = None
) -> dict[str, str]:
    """Export mcpd configuration files as sanitized artifacts.

    Attempts to parse mcpd config (.mcpd.toml) contents from the supplied Agent Factory outputs,
    which is used to generate portable configuration files that separate the configuration structure
    from sensitive values, making the generated agent more portable while protecting secrets.

    The portable configuration files only handle required variables (not optional ones) for an MCP server.

    Args:
        agent_factory_outputs: The outputs from the Agent Factory which should contain a key named `mcpd`
            the value should be string contents representing the mcpd configuration file (.mcpd.toml).
        output_dir: Optional path to use as output directory for generated files.
            If None, a temporary directory will be created and automatically cleaned up.
            If provided, the directory and its contents will be preserved for further use (this causes a side effect).

    Returns:
        Dictionary with exported configuration artifacts.
        May contain:
            - ".mcpd.toml": The original mcpd configuration file content.
            - ".env": Environment contract with placeholders for required variables.
            - "secrets.prod.toml": Sanitized execution context safe for version control.
        Or an empty dictionary when the mcpd configuration doesn't exist in the supplied Agent Factory outputs.

    Note:
        If mcpd export fails, warnings are logged but the function continues.
        When output_dir is None, temporary files are cleaned up automatically.
        When output_dir is provided, all generated files remain in the specified directory (not recommended).
    """
    exported_artifacts = {}

    mcpd_toml = agent_factory_outputs.get("mcpd")
    if not (mcpd_toml and mcpd_toml.strip()):
        logger.warning("'Agent Factory output does not contain 'mcpd' config, no related artifacts will be exported.")
        return exported_artifacts

    # Expected file names.
    config_file_name = ".mcpd.toml"
    contract_file_name = ".env"
    context_file_name = "secrets.prod.toml"

    # Use provided output_dir or create a temporary directory that will auto-cleanup.
    context = tempfile.TemporaryDirectory() if output_dir is None else nullcontext(output_dir)

    with context as working_dir:
        work_dir = Path(working_dir) if working_dir else output_dir

        try:
            # Include the original mcpd config file in the export.
            exported_artifacts[config_file_name] = mcpd_toml

            # Write the mcpd config file to a temporary file so it can be used by mcpd binary to export config.
            mcpd_toml_path = work_dir / config_file_name
            mcpd_toml_path.write_text(mcpd_toml, encoding="utf-8")

            # Prepare export paths.
            mcpd_contract_path = work_dir / contract_file_name
            mcpd_context_path = work_dir / context_file_name

            # Run 'mcpd config export' to generate artifacts.
            run_binary(
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

            # Read the generated contract file (.env).
            if mcpd_contract_path.exists():
                exported_artifacts[contract_file_name] = mcpd_contract_path.read_text(encoding="utf-8")
            else:
                logger.warning(f"mcpd config export did not generate expected contract file: {mcpd_contract_path}")

            # Read the generated context file (secrets.prod.toml).
            if mcpd_context_path.exists():
                exported_artifacts[context_file_name] = mcpd_context_path.read_text(encoding="utf-8")
            else:
                logger.warning(f"mcpd config export did not generate expected context file: {mcpd_context_path}")

        except (RuntimeError, ValueError) as e:
            logger.warning(f"Failed to export mcpd config: {e}")

    return exported_artifacts


def parse_cli_args_to_params_json(cli_args_str: str) -> str:
    """Parse CLI arguments into the schema format the platform expects
    Example: "url: str" -> {"params": {"--url": "string"}}
    """
    params_dict = {}
    if cli_args_str:
        for arg in cli_args_str.split(","):
            arg = arg.strip()
            if ":" in arg:
                name, arg_type = arg.split(":", 1)
                name = name.strip()
                arg_type = arg_type.strip()
                param_name = f"--{name}"

                if arg_type == "str":
                    param_type = "string"
                elif arg_type == "int":
                    param_type = "integer"
                elif arg_type == "float":
                    param_type = "number"
                elif arg_type == "bool":
                    param_type = "boolean"
                else:
                    param_type = "string"
                params_dict[param_name] = param_type

    agent_parameters = AgentParameters(params=params_dict)
    return agent_parameters.model_dump_json()


def prepare_agent_artifacts(agent_factory_outputs: dict[str, str]) -> dict[str, str]:
    """Prepares the agent outputs (based on AgentFactoryOutputs)
    for saving by filling in the code generation templates
    and gathering (Python) tool files.
    """
    artifacts_to_save = {}
    agent_code = AGENT_CODE_TEMPLATE.format(**agent_factory_outputs)
    clean_agent_code = clean_python_code_with_autoflake(agent_code)
    validated_dependencies = validate_dependencies(agent_factory_outputs)

    artifacts_to_save["agent.py"] = clean_agent_code
    artifacts_to_save["README.md"] = agent_factory_outputs["readme"]
    artifacts_to_save["requirements.txt"] = validated_dependencies

    # Identify and read tool files
    for tool_file in TOOLS_DIR.iterdir():
        if tool_file.is_file() and (tool_file.stem in agent_code or tool_file.name == "__init__.py"):
            artifacts_to_save[f"tools/{tool_file.name}"] = tool_file.read_text(encoding="utf-8")

    cli_args_str = agent_factory_outputs.get("cli_args", "")
    artifacts_to_save["agent_parameters.json"] = parse_cli_args_to_params_json(cli_args_str)

    # Export mcpd config and sanitized artifacts for portability
    mcpd_artifacts = export_mcpd_config_artifacts(agent_factory_outputs)
    artifacts_to_save.update(mcpd_artifacts)

    # Add a .gitignore file for ignoring secrets
    artifacts_to_save[".gitignore"] = "*secrets*.dev.toml\n!secrets.prod.toml"

    return artifacts_to_save


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
            return {}
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
