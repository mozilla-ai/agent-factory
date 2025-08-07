import json
import subprocess
from pathlib import Path

from agent_factory.instructions import AGENT_CODE_TEMPLATE
from agent_factory.schemas import AgentParameters
from agent_factory.utils import clean_python_code_with_autoflake
from agent_factory.utils.logging import logger

TOOLS_DIR = Path(__file__).parent.parent / "tools"
BINARY_NAME_MCPD = "mcpd"


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

    artifacts_to_save["agent.py"] = clean_agent_code
    artifacts_to_save["README.md"] = agent_factory_outputs["readme"]
    artifacts_to_save["requirements.txt"] = agent_factory_outputs["dependencies"]

    # Identify and read tool files
    for tool_file in TOOLS_DIR.iterdir():
        if tool_file.is_file() and (tool_file.stem in agent_code or tool_file.name == "__init__.py"):
            artifacts_to_save[f"tools/{tool_file.name}"] = tool_file.read_text(encoding="utf-8")

    cli_args_str = agent_factory_outputs.get("cli_args", "")
    artifacts_to_save["agent_parameters.json"] = parse_cli_args_to_params_json(cli_args_str)

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
