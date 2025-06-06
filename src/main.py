import json
import shutil
import uuid
from datetime import datetime
from pathlib import Path

import dotenv
import fire
from any_agent import AgentConfig, AgentFramework, AnyAgent
from any_agent.config import MCPStdio
from any_agent.tools import search_tavily, visit_webpage
from pydantic import BaseModel, Field
from src.instructions import INSTRUCTIONS

dotenv.load_dotenv()

repo_root = Path.cwd()
workflows_root = repo_root / "generated_workflows"
tools_dir = repo_root / "tools"
mcps_dir = repo_root / "mcps"


class AgentFactoryOutputs(BaseModel):
    agent_code: str = Field(..., description="The agent code in Markdown format")
    run_instructions: str = Field(..., description="The run instructions in Markdown format")
    dependencies: str = Field(..., description="The dependencies line by line in Markdown format")


def get_mount_config():
    return {
        "host_tools_dir": str(tools_dir),
        "host_mcps_dir": str(mcps_dir),
        "container_tools_dir": "/app/tools",
        "container_mcps_dir": "/app/mcps",
        "file_ops_dir": "/app",
    }


def get_default_tools(mount_config):
    return [
        visit_webpage,
        search_tavily,
        MCPStdio(
            command="docker",
            args=[
                "run",
                "-i",
                "--rm",
                "--volume",
                "/app",
                # Mount tools directory
                "--mount",
                f"type=bind,src={mount_config['host_tools_dir']},dst={mount_config['container_tools_dir']}",
                # Mount mcps directory
                "--mount",
                f"type=bind,src={mount_config['host_mcps_dir']},dst={mount_config['container_mcps_dir']}",
                "mcp/filesystem",
                mount_config["file_ops_dir"],
            ],
            tools=[
                "read_file",
                "search_files",
                "list_allowed_directories",
                "list_directory",
            ],
        ),
    ]


def validate_agent_outputs(str_output: str):
    try:
        json_output = json.loads(str_output)
        agent_factory_outputs = AgentFactoryOutputs.model_validate(json_output)
    except Exception as e:
        raise ValueError(
            f"Invalid format received for agent outputs: {e}. Could not parse the output as AgentFactoryOutputs."
        ) from e
    return agent_factory_outputs


def remove_markdown_code_block_delimiters(text: str) -> str:
    """Remove backticks from the start and end of markdown output."""
    text = text.strip()
    if text.startswith("```") and text.endswith("```"):
        lines = text.splitlines()
        return "\n".join(lines[1:-1])
    return text


def save_agent_raw_output(output: str, generated_workflows_dir: str = "latest"):
    """Save the agent_trace.final_output to a file. For debugging in case the output is not parsed correctly"""
    save_artifacts_dir = workflows_root / generated_workflows_dir
    Path(save_artifacts_dir).mkdir(exist_ok=True)
    agent_factory_raw_output_path = Path(f"{save_artifacts_dir}/agent_factory_raw_output.txt")
    with agent_factory_raw_output_path.open("w", encoding="utf-8") as f:
        f.write(output)
    print(f"Raw agent output saved to {agent_factory_raw_output_path}")


def save_agent_parsed_outputs(output: AgentFactoryOutputs, generated_workflows_dir: str = "latest"):
    """Save all three outputs from AgentFactoryOutputs to separate files."""
    save_artifacts_dir = workflows_root / generated_workflows_dir
    Path(save_artifacts_dir).mkdir(exist_ok=True)

    agent_path = Path(f"{save_artifacts_dir}/agent.py")
    instructions_path = Path(f"{save_artifacts_dir}/INSTRUCTIONS.md")
    requirements_path = Path(f"{save_artifacts_dir}/requirements.txt")

    with agent_path.open("w", encoding="utf-8") as f:
        f.write(remove_markdown_code_block_delimiters(output.agent_code))

    with instructions_path.open("w", encoding="utf-8") as f:
        f.write(output.run_instructions)

    with requirements_path.open("w", encoding="utf-8") as f:
        f.write(remove_markdown_code_block_delimiters(output.dependencies))

    print(f"Files saved to {save_artifacts_dir}")


def setup_directories(workflows_root, workflow_dir):
    workflows_root.mkdir(parents=True, exist_ok=True)
    workflow_dir.mkdir(parents=True, exist_ok=True)
    latest_dir = workflows_root / "latest"
    archive_root = workflows_root / "archive"
    latest_dir.mkdir(parents=True, exist_ok=True)
    archive_root.mkdir(parents=True, exist_ok=True)
    return latest_dir, archive_root


def create_agent(mount_config):
    framework = AgentFramework.OPENAI
    agent = AnyAgent.create(
        framework,
        AgentConfig(
            model_id="gpt-4.1",
            instructions=INSTRUCTIONS,
            tools=get_default_tools(mount_config),
        ),
    )
    return agent


def build_run_instructions(user_prompt):
    return f"""
    ## Tools
    You may use appropriate tools provided from tools/available_tools.md in the agent configuration.
    In addition to the tools pre-defined in available_tools.md,
    two other tools that you could use in the agent configuration are search_web, search_tavily and visit_webpage.

    ## MCPs
    You may use appropriate MCPs provided from mcps/available_mcps.md in the agent configuration.

    You may use the following tools to browse and view the contents of the tools/ and mcps/ directories:
    - list_directory tool to list the contents of the tools/ and mcps/ directories
    - read_file tool to read the contents of the available_tools.md and available_mcps.md files
    - search_files tool to recursively search for files/directories
    - list_allowed_directories tool to list all directories that you have access to

    Generate python code for an agentic workflow using any-agent library to be able to do the following:
    {user_prompt}
    """


def save_agent_trace(agent_trace, latest_dir):
    agent_trace_path_latest = latest_dir / "agent_factory_trace.json"
    with Path.open(agent_trace_path_latest, "w", encoding="utf-8") as f:
        f.write(agent_trace.model_dump_json(indent=2))


def archive_latest_run_artifacts(latest_dir, archive_dir):
    for item in latest_dir.iterdir():
        if item.is_file():
            shutil.copy(item, archive_dir / item.name)
        else:
            print(f"Skipping directory: {item.name}")


def main(user_prompt: str, workflow_dir: Path | None = None):
    """Generate python code for an agentic workflow based on the user prompt."""
    workflow_id = str(uuid.uuid4())
    if workflow_dir is None:
        workflow_dir = workflows_root / "latest"
    else:
        workflow_dir = Path(workflow_dir)

    latest_dir, archive_root = setup_directories(workflows_root, workflow_dir)
    timestamp_id = datetime.now().strftime("%Y-%m-%d_%H:%M:%S") + "_" + workflow_id[:8]
    archive_dir = archive_root / timestamp_id
    archive_dir.mkdir(parents=True, exist_ok=True)

    mount_config = get_mount_config()
    agent = create_agent(mount_config)
    run_instructions = build_run_instructions(user_prompt)

    agent_trace = agent.run(run_instructions, max_turns=30)
    save_agent_trace(agent_trace, latest_dir)

    # Save structured agent outputs
    # Save raw agent output for debugging
    save_agent_raw_output(agent_trace.final_output, latest_dir)
    # Validate and save parsed agent outputs
    agent_factory_outputs = validate_agent_outputs(agent_trace.final_output)
    save_agent_parsed_outputs(agent_factory_outputs, latest_dir)

    archive_latest_run_artifacts(latest_dir, archive_dir)

    print(f"Workflow files saved in: {latest_dir} and archived in {archive_dir}")
    print(agent_factory_outputs)


if __name__ == "__main__":
    fire.Fire(main)
