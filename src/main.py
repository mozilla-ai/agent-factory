import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path

import dotenv
import fire
from any_agent import AgentConfig, AgentFramework, AnyAgent
from any_agent.config import MCPStdio
from any_agent.tools import visit_webpage
from src.instructions import INSTRUCTIONS

dotenv.load_dotenv()

repo_root = Path.cwd()
workflows_root = repo_root / "generated_workflows"
tools_dir = repo_root / "tools"
mcps_dir = repo_root / "mcps"


def get_mount_config():
    return {
        "host_workflows_dir": str(workflows_root),
        "host_tools_dir": str(tools_dir),
        "host_mcps_dir": str(mcps_dir),
        "container_workflows_dir": "/app/generated_workflows",
        "container_tools_dir": "/app/tools",
        "container_mcps_dir": "/app/mcps",
        "file_ops_dir": "/app",
    }


def get_default_tools(mount_config):
    return [
        visit_webpage,
        MCPStdio(
            command="docker",
            args=[
                "run",
                "-i",
                "--rm",
                "-e",
                "BRAVE_API_KEY",
                "mcp/brave-search",
            ],
            env={
                "BRAVE_API_KEY": os.getenv("BRAVE_API_KEY"),
            },
            tools=[
                "brave_web_search",
            ],
        ),
        MCPStdio(
            command="docker",
            args=[
                "run",
                "-i",
                "--rm",
                "--volume",
                "/app",
                # Mount workflows directory
                "--mount",
                f"type=bind,src={mount_config['host_workflows_dir']},dst={mount_config['container_workflows_dir']}",
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
                "write_file",
                "list_directory",
            ],
        ),
    ]


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


def build_run_instructions(user_prompt, container_workflow_dir):
    return f"""
    Generate python code for an agentic workflow using any-agent library to be able to do the following:
    {user_prompt}

    ## Tools
    You may use appropriate tools provided from tools/available_tools.md in the agent configuration.
    In addition to the tools pre-defined in available_tools.md,
    two other tools that you could use are search_web and visit_webpage.

    ## MCPs
    You may use appropriate MCPs provided from mcps/available_mcps.md in the agent configuration.

    ## File Saving Instructions
    YOU MUST save all generated files (including agent.py, INSTRUCTIONS.md, requirements.txt)
    inside the directory: `{container_workflow_dir}`. For example, save agent.py as `{container_workflow_dir}/agent.py`.
    Double check that the saved files exist using list_directory tool before stopping.
    """


def save_agent_trace(agent_trace, latest_dir):
    agent_trace_path_latest = latest_dir / "agent_trace.json"
    with Path.open(agent_trace_path_latest, "w", encoding="utf-8") as f:
        f.write(agent_trace.model_dump_json(indent=2))


def archive_latest(latest_dir, archive_dir):
    for item in latest_dir.iterdir():
        shutil.copy(item, archive_dir / item.name)


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
    container_workflow_dir = mount_config["container_workflows_dir"] + "/latest"
    run_instructions = build_run_instructions(user_prompt, container_workflow_dir)

    agent_trace = agent.run(run_instructions, max_turns=30)
    save_agent_trace(agent_trace, latest_dir)
    archive_latest(latest_dir, archive_dir)

    print(f"Workflow files saved in: {latest_dir} and archived in {archive_dir}")
    print(agent_trace.final_output)


if __name__ == "__main__":
    fire.Fire(main)
