from pathlib import Path

from any_agent import AgentConfig, AgentFramework, AnyAgent
from any_agent.config import MCPStdio
from any_agent.tools import search_web, visit_webpage
from src.instructions import INSTRUCTIONS

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

RUN_INSTRUCTIONS = """
Generate python code using any-agent library that I can run to summarize text content from a given webpage URL.
Use approriate tools from tools/available_tools.py
"""
agent_trace = agent.run(RUN_INSTRUCTIONS, max_turns=20)
print(agent_trace.final_output)
