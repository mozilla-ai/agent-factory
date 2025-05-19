from pathlib import Path
from any_agent import AgentConfig, AgentFramework, AnyAgent
from any_agent.config import MCPStdio
from any_agent.tools import search_web, visit_webpage
from src.instructions import INSTRUCTIONS

repo_root = Path.cwd()
outputs_dir = "generated_workflows"
workflows_dir = repo_root / outputs_dir

# Create a separate directory for file operations
file_ops_dir = "/app"
mount_dir = "/app/generated_workflows"


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
                    "--volume", "/app",
                    "--mount",
                    f"type=bind,src={workflows_dir},dst={mount_dir}",
                    "mcp/filesystem",
                    file_ops_dir,
                ],
                tools=[
                    "write_file",
                ],
            ),
        ],
    ),
)

RUN_INSTRUCTIONS = """
Generate python code using any-agent library that I can run to search for the best sushi restaurant in Berlin using OpenAI agents.
"""
agent_trace = agent.run(RUN_INSTRUCTIONS, max_turns=20)
print(agent_trace.final_output)
