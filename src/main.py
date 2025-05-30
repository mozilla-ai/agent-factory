import os
import uuid
from pathlib import Path

import dotenv
import fire
from any_agent import AgentConfig, AgentFramework, AnyAgent
from any_agent.config import MCPStdio
from any_agent.tools import visit_webpage
from src.instructions import INSTRUCTIONS

dotenv.load_dotenv()


def main(user_prompt: str, workflow_dir: Path = Path()) -> None:
    """Generate python code for an agentic workflow based on the user prompt.

    Args:
        user_prompt: The user's prompt describing what the agentic workflow should do.
        workflow_dir: Optional. Path to the workflow directory. If not provided, a new one is created.

    Returns:
        The final output from the agent.
    """
    repo_root = Path.cwd()
    workflows_root = repo_root / "generated_workflows"
    tools_dir = repo_root / "tools"
    mcps_dir = repo_root / "mcps"

    session_id = str(uuid.uuid4())
    # Create a unique workflow directory if not provided
    if workflow_dir is None:
        workflow_dir = workflows_root / f"workflow_{session_id}"

    # Create generated_workflows directory if it doesn't exist
    workflows_root.mkdir(parents=True, exist_ok=True)
    workflow_dir.mkdir(parents=True, exist_ok=True)

    # Create a separate directory for file operations
    file_ops_dir = "/app"
    mount_workflows_dir = "/app/generated_workflows"
    mount_tools_dir = "/app/tools"
    mount_mcps_dir = "/app/mcps"

    framework = AgentFramework.OPENAI
    agent = AnyAgent.create(
        framework,
        AgentConfig(
            model_id="gpt-4.1",
            instructions=INSTRUCTIONS,
            tools=[
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
                        f"type=bind,src={workflows_root},dst={mount_workflows_dir}",
                        # Mount tools directory
                        "--mount",
                        f"type=bind,src={tools_dir},dst={mount_tools_dir}",
                        # Mount mcps directory
                        "--mount",
                        f"type=bind,src={mcps_dir},dst={mount_mcps_dir}",
                        "mcp/filesystem",
                        file_ops_dir,
                    ],
                    tools=[
                        "read_file",
                        "write_file",
                        "list_directory",
                    ],
                ),
            ],
        ),
    )

    # Get the workflow subdirectory name (e.g., "workflow_xxx")
    workflow_subdir = f"{workflow_dir.name}/{session_id}"
    container_workflow_dir = f"/app/generated_workflows/{workflow_subdir}"

    run_instructions = f"""
    Generate python code for an agentic workflow using any-agent library to be able to do the following:
    {user_prompt}

    ## Tools
    You may use appropriate tools provided from tools/available_tools.md in the agent configuration.
    In addition to the tools pre-defined in available_tools.md,
    two other tools that you could use are search_web and visit_webpage.

    ## MCPs
    You may use appropriate MCPs provided from mcps/available_mcps.md in the agent configuration.

    ## File Saving Instructions
    YOU MUST save all generated files (including agent.py, INSTRUCTIONS.md, requirements.txt, etc.)
    inside the directory: `{container_workflow_dir}`. For example, save agent.py as `{container_workflow_dir}/agent.py`.
    Double check that the saved files exist using list_directory tool before stopping.
    """
    agent_trace = agent.run(run_instructions, max_turns=30)

    # When saving files, use workflow_dir instead of workflows_root
    agent_trace_path = workflow_dir / "agent_trace.json"
    # agent_py_path = workflow_dir / "agent.py"
    # instructions_md_path = workflow_dir / "INSTRUCTIONS.md"
    # requirements_txt_path = workflow_dir / "requirements.txt"

    # Example: Save agent trace
    with Path.open(agent_trace_path, "w", encoding="utf-8") as f:
        f.write(agent_trace.model_dump_json(indent=2))

    print(f"Workflow files saved in: {workflow_dir}")
    print(agent_trace.final_output)


if __name__ == "__main__":
    fire.Fire(main)
