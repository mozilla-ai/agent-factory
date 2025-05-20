from pathlib import Path

import fire
from any_agent import AgentConfig, AgentFramework, AnyAgent
from any_agent.config import MCPStdio
from any_agent.tools import search_web, visit_webpage
from src.instructions import INSTRUCTIONS


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

    # Create a separate directory for file operations
    file_ops_dir = "/app"
    mount_workflows_dir = "/app/generated_workflows"
    mount_tools_dir = "/app/tools"

    framework = AgentFramework.OPENAI
    agent = AnyAgent.create(
        framework,
        AgentConfig(
            model_id="gpt-4.1",
            instructions=INSTRUCTIONS,
            tools=[
                search_web,
                visit_webpage,
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
    You may use appropriate tools provided from tools/available_tools.md in the agent configuration.
    In addition to the tools pre-defined in available_tools.md,
    two other tools that you could use are search_web and visit_webpage.
    """
    agent_trace = agent.run(run_instructions, max_turns=20)
    print(agent_trace.final_output)
    return agent_trace.final_output


if __name__ == "__main__":
    fire.Fire(main)
