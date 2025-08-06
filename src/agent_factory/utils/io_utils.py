import json
import subprocess
import uuid
from datetime import datetime
from pathlib import Path

from agent_factory.instructions import AGENT_CODE_TEMPLATE
from agent_factory.schemas import AgentParameters
from agent_factory.utils import clean_python_code_with_autoflake
from agent_factory.utils.logging import logger

BINARY_NAME_MCPD = "mcpd"


def setup_output_directory(output_dir: Path | None = None) -> Path:
    if output_dir is None:
        output_dir = Path.cwd()
        uid = datetime.now().strftime("%Y-%m-%d_%H:%M:%S") + "_" + str(uuid.uuid4())[:8]
        # store in a unique dir under generated_workflows by default
        output_dir = output_dir / "generated_workflows" / uid
    else:
        # guarantee output_dir is PosixPath
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def save_agent_outputs(result: dict[str, str], output_dir: Path) -> None:
    """Save the agent outputs to files.

    This function takes a dictionary containing the agent outputs and saves them to
    an output directory. It creates four different files in the output directory:
        - agent.py: Contains the agent code.
        - README.md: Contains the run instructions in Markdown format.
        - requirements.txt: Contains the dependencies line by line.
        - agent_parameters.json: Contains the CLI parameters as JSON.

    Args:
        result: A dictionary containing the agent outputs. It should include the following keys:
            - agent_code: The Python code for the agent.
            - readme: The instructions for running the agent in Markdown format.
            - dependencies: A string containing the dependencies required by the agent, one per line.
            - cli_args: The CLI arguments for the agent.
        output_dir: The output directory to save the agent outputs.

    Raises:
        Exception: If there is an error while writing the files to the output directory.
    """
    try:
        agent_path = output_dir / "agent.py"
        readme_path = output_dir / "README.md"
        requirements_path = output_dir / "requirements.txt"
        agent_parameters_path = output_dir / "agent_parameters.json"
        tools_dir_path = output_dir / "tools"
        tools_dir_path.mkdir(exist_ok=True)
        agent_code = f"{AGENT_CODE_TEMPLATE.format(**result)}"

        clean_agent_code = clean_python_code_with_autoflake(agent_code)

        with agent_path.open("w", encoding="utf-8") as f:
            f.write(clean_agent_code)

        with readme_path.open("w", encoding="utf-8") as f:
            f.write(result["readme"])

        with requirements_path.open("w", encoding="utf-8") as f:
            f.write(result["dependencies"])

        cli_args_str = result.get("cli_args", "")
        # Parse CLI arguments into the schema format the platform expects
        # Example: "url: str" -> {"params": {"--url": "string"}}
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

        with agent_parameters_path.open("w", encoding="utf-8") as f:
            json.dump(agent_parameters.model_dump(), f, indent=2)

        tools_dir = Path("src/agent_factory/tools")
        for tool_file in tools_dir.iterdir():
            if tool_file.is_file() and (tool_file.stem in agent_code or tool_file.name == "__init__.py"):
                tool_destination = tools_dir_path / tool_file.name
                # Copy the tool file to the output directory
                tool_destination.write_text(tool_file.read_text(encoding="utf-8"), encoding="utf-8")

        logger.info(f"Agent files saved to {output_dir}")

    except Exception as e:
        logger.warning(f"Warning: Failed to parse and save agent outputs: {str(e)}")


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
