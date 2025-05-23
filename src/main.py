import os
from pathlib import Path

import dotenv
import fire
from any_agent import AgentConfig, AgentFramework, AnyAgent
from any_agent.config import MCPStdio
from any_agent.tools import visit_webpage
from src.instructions import INSTRUCTIONS

dotenv.load_dotenv()


def main(user_prompt: str):
    """Generate python code for an agentic workflow based on the user prompt.

    Args:
        user_prompt: The user's prompt describing what the agentic workflow should do.

    Returns:
        The final output from the agent.
    """
    repo_root = Path.cwd()
    workflows_dir = repo_root / "generated_workflows"
    tools_dir = repo_root / "tools"
    mcps_dir = repo_root / "mcps"

    # Create generated_workflows directory if it doesn't exist
    workflows_dir.mkdir(parents=True, exist_ok=True)

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
                        f"type=bind,src={workflows_dir},dst={mount_workflows_dir}",
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

    run_instructions = f"""
    Generate python code for an agentic workflow using any-agent library to be able to do the following:
    {user_prompt}

    ## Tools
    You may use appropriate tools provided from tools/available_tools.md in the agent configuration.
    In addition to the tools pre-defined in available_tools.md,
    two other tools that you could use are search_web and visit_webpage.

    ## MCPs
    You may use appropriate MCPs provided from mcps/available_mcps.md in the agent configuration.

    You MUST save the generated python code as `agent.py` and associated files, following the file saving instructions.
    """
    agent_trace = agent.run(run_instructions, max_turns=30)

    print(agent_trace.final_output)


if __name__ == "__main__":
    fire.Fire(main)
