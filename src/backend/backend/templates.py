USER_PROMPT = """Generate Python code for an agentic workflow using the `any-agent` library
to do the following:
{0}

Use appropriate tools in the agent configuration:
- Select relevant tools from `tools/available_tools.md`.
- Use the `search_mcp_servers` tool to discover and add MCP servers that provide relevant tools
    to the configuration.

Always use the simplest and most efficient tools available for the task.
"""


AGENT_CODE_TEMPLATE = """
# agent.py

# good to have
import os

# ALWAYS used
from dotenv import load_dotenv
from any_agent import AgentConfig, AnyAgent, AgentRunError
from any_agent.serving import A2AServingConfig
from any_agent.config import MCPStdio
from pydantic import BaseModel, Field
from fire import Fire

# ADD BELOW HERE: tools made available by any-agent or agent-factory
{imports}

load_dotenv()

# ========== Structured output definition ==========
{structured_outputs}

# ========== System (Multi-step) Instructions ===========
INSTRUCTIONS='''
{agent_instructions}
'''

# ========== Tools definition ===========
{tools}


# ========== Running the agent via A2AServing ===========
def main(
    framework: str = "openai",
    model: str = "o3",
    host: str = "localhost",
    port: int = 8080,
    log_level: str = "info",
):
    \"\"\"{agent_description}\"\"\"
    agent = AnyAgent.create(
        framework,
        AgentConfig(
            model_id=model,
            instructions=INSTRUCTIONS,
            tools=TOOLS,
            model_args={{"tool_choice": "required"}},
            output_type=StructuredOutput,
        ),
    )

    agent.serve(A2AServingConfig(host=host, port=port, log_level=log_level))


if __name__ == "__main__":
    Fire(main)

"""


DOCKERFILE_TEMPLATE = """
FROM python:3.13.5-slim

ENV FRAMEWORK=openai
ENV MODEL=o3
ENV HOST=0.0.0.0
ENV PORT=8080
ENV LOG_LEVEL=info

WORKDIR /app

RUN pip install uv

COPY . /app

EXPOSE 8080

CMD ["sh", "-c", "uv run --with-requirements requirements.txt --python 3.13 python \
     agent.py \
     --framework ${FRAMEWORK} --model ${MODEL} --host ${HOST} --port ${PORT} --log-level ${LOG_LEVEL}"]
"""
