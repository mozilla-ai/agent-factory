TOOLS_REMINDER = """Use appropriate tools in the agent configuration:
- Select relevant tools from `tools/available_tools.md`.
- Use the `search_mcp_servers` tool to discover and add MCP servers that provide relevant tools
    to the configuration.

Always use the simplest and most efficient tools available for the task.
"""


USER_PROMPT = """Generate Python code for an agentic workflow using the `any-agent` library
to do the following:
{0}

{1}
"""


AGENT_CODE_TEMPLATE = """
# agent.py

# good to have
import os

# ALWAYS used
from dotenv import load_dotenv
from any_agent import AgentConfig, AnyAgent, AgentRunError
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

agent = AnyAgent.create(
    "openai",
    AgentConfig(
        model_id="o3",
        instructions=INSTRUCTIONS,
        tools=TOOLS,
        output_type=StructuredOutput,
        model_args={{"tool_choice": "required"}},
    ),
)

def run_agent({cli_args}):
    \"\"\"{agent_description}\"\"\"
    input_prompt = f"{prompt_template}"
    try:
        agent_trace = agent.run(prompt=input_prompt, max_turns=20)
    except AgentRunError as e:
        agent_trace = e.trace
        print(f"Agent execution failed: {{str(e)}}")
        print("Retrieved partial agent trace...")
    with open("generated_workflows/latest/agent_eval_trace.json", "w", encoding="utf-8") as f:
        f.write(agent_trace.model_dump_json(indent=2))
    return agent_trace.final_output

if __name__ == "__main__":
    Fire(run_agent)

"""
