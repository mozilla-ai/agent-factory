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
