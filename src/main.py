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
Refer to the any-agent docs for more information. Suggest a suitable instruction prompt and model for the agent.
I would like the agent to use the `output_type` argument to obtain structured output from the agent based on predefined Pydantic models.

Finally save the code in a file named `agent.py`. The run instructions should be made available in INSTRUCTIONS.md.
"""
agent_trace = agent.run(RUN_INSTRUCTIONS)
print(agent_trace.final_output)
