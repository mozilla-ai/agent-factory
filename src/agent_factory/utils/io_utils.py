import uuid
from datetime import datetime
from pathlib import Path

from agent_factory.instructions import AGENT_CODE_TEMPLATE
from agent_factory.utils import clean_python_code_with_autoflake

TOOLS_DIR = Path(__file__).parent.parent / "tools"


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

    return artifacts_to_save
