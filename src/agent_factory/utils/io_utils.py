import uuid
from datetime import datetime
from pathlib import Path

from agent_factory.instructions import AGENT_CODE_TEMPLATE
from agent_factory.utils import clean_python_code_with_autoflake
from agent_factory.utils.logging import logger


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
    an output directory. It creates three different files in the output directory:
        - agent.py: Contains the agent code.
        - README.md: Contains the run instructions in Markdown format.
        - requirements.txt: Contains the dependencies line by line.

    Args:
        result: A dictionary containing the agent outputs. It should include the following keys:
            - agent_code: The Python code for the agent.
            - readme: The instructions for running the agent in Markdown format.
            - dependencies: A string containing the dependencies required by the agent, one per line.

    Raises:
        Exception: If there is an error while writing the files to the output directory.
    """
    try:
        agent_path = output_dir / "agent.py"
        readme_path = output_dir / "README.md"
        requirements_path = output_dir / "requirements.txt"
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

        tools_dir = Path("src/agent_factory/tools")
        for tool_file in tools_dir.iterdir():
            if tool_file.is_file() and (tool_file.stem in agent_code or tool_file.name == "__init__.py"):
                tool_destination = tools_dir_path / tool_file.name
                # Copy the tool file to the output directory
                tool_destination.write_text(tool_file.read_text(encoding="utf-8"), encoding="utf-8")

        logger.info(f"Agent files saved to {output_dir}")

    except Exception as e:
        logger.warning(f"Warning: Failed to parse and save agent outputs: {str(e)}")
