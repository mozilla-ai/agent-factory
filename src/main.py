import os

from any_agent import AgentConfig, AgentFramework, AnyAgent
from any_agent.config import MCPStdio
from any_agent.tools import search_web, visit_webpage

from instructions import INSTRUCTIONS

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
                    "--mount",
                    f"type=bind,src={os.getcwd()}/generated_workflows,dst=/projects",
                    "mcp/filesystem",
                    "/projects",
                ],
                tools=[
                    "write_file",
                ],
            ),
        ],
    ),
)

RUN_INSTRUCTIONS = """
Generate python code using any-agent library that I can run to search for the best sushi restaurant in Berlin using openai agents.
"""
agent_trace = agent.run(RUN_INSTRUCTIONS, max_turns=20)
print(agent_trace.final_output)
