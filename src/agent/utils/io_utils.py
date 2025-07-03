import uuid
from datetime import datetime
from pathlib import Path

from instructions import AGENT_CODE_TEMPLATE, AGENT_CODE_TEMPLATE_RUN_VIA_A2A
from utils.logging import logger


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
    output_dir = setup_output_directory()
    try:
        agent_path = output_dir / "agent.py"
        instructions_path = output_dir / "INSTRUCTIONS.md"
        requirements_path = output_dir / "requirements.txt"
        agent_code = f"{AGENT_CODE_TEMPLATE.format(**result)} \n{AGENT_CODE_TEMPLATE_RUN_VIA_A2A.format(**result)}"

        with agent_path.open("w", encoding="utf-8") as f:
            f.write(agent_code)

        with instructions_path.open("w", encoding="utf-8") as f:
            f.write(result["run_instructions"])

        with requirements_path.open("w", encoding="utf-8") as f:
            f.write(result["dependencies"])

        logger.info(f"Agent files saved to {output_dir}")

    except Exception as e:
        print(f"Warning: Failed to parse and save agent outputs: {str(e)}")
