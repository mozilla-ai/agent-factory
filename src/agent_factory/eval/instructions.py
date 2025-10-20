"""Instructions for the agent evaluation JSON generator.
The structured JSON output is saved as JSON format.
"""

from jinja2 import Template

EVALUATION_CATEGORIES = """
1. **Tool Usage**: Verify correct tool selection and invocation for each sub-task
2. **Information Retrieval**: Ensure all necessary data is gathered
3. **Data Processing**: Check calculations, unit conversions, information synthesis
4. **Logic & Reasoning**: Assess problem decomposition and step sequencing
5. **Output Quality**: Evaluate answer completeness and accuracy
"""

AGENT_SCRIPT_AND_JSON_EXAMPLE = """
**Agent Script:**
```python
# agent.py

# Always used imports
import json  # noqa: I001
import os
import sys
from pathlib import Path

from any_agent import AgentConfig, AgentRunError, AnyAgent
from dotenv import load_dotenv
from fire import Fire
from mcpd import McpdClient, McpdError
from pydantic import BaseModel, Field

# ADD BELOW HERE: tools made available by agent-factory
from tools.review_code_with_llm import review_code_with_llm
from tools.search_tavily import search_tavily

load_dotenv()

# Connect to mcpd daemon for accessing available tools
MCPD_ENDPOINT = os.getenv("MCPD_ADDR", "http://localhost:8090")
MCPD_API_KEY = os.getenv("MCPD_API_KEY", None)

# ========== Structured output definition ==========
class StructuredOutput(BaseModel):
    code: str = Field(..., description="The code to be reviewed.")
    review: str = Field(..., description="The review of the code.")

# ========= System Instructions =========
INSTRUCTIONS = "Example instructions"

# ========== Tools definition ===========
TOOLS = [
    search_tavily,  # Example tool taken from tools/README.md
    review_code_with_llm,  # Example tool taken from tools/README.md
]

# Connect to any running MCP servers via mcpd
try:
    mcpd_client = McpdClient(api_endpoint=MCPD_ENDPOINT, api_key=MCPD_API_KEY)
    mcp_server_tools = mcpd_client.agent_tools()
    if not mcp_server_tools:
        print("No tools found via mcpd.")
    TOOLS.extend(mcp_server_tools)
except McpdError as e:
    print(
        f"Error connecting to mcpd: {e}. If the agent doesn't use any MCP servers you can safely ignore this error",
        file=sys.stderr
    )

# ========== Running the agent via CLI ===========
agent = AnyAgent.create(
    "openai",
    AgentConfig(
        model_id="o3",
        instructions=INSTRUCTIONS,
        tools=TOOLS,
        output_type=StructuredOutput,
        model_args={"tool_choice": "auto"},
    ),
)

# Running the agent
user_input = "Example user input code to be reviewed"
agent.run(prompt=user_input)

```

**Generated JSON:**
```json
{
  "criteria": [
      "Ensure that the agent called `search_tavily` or another search tool to find relevant information about code
      review best practices or specific technologies mentioned in the code.",
      "Ensure that the agent called `review_code_with_llm` to perform the actual code analysis and review.",
      "Verify that the agent correctly identified the programming language and framework/libraries used in the provided
      code.",
      "Check that the agent's review covers multiple aspects such as code quality, security, performance, and best
      practices.",
      "Ensure that the agent searched for current standards or documentation related to the specific technologies or
      patterns found in the code.",
      "Verify that the agent's output follows the required StructuredOutput structure with both 'code' and 'review'
      fields properly populated.",
      "Check that the review includes specific, actionable recommendations for code improvement.",
      "Ensure that the agent appropriately utilized the available MCP tools (brave_web_search) when additional context
      or verification was needed.",
      "Verify that the final review demonstrates understanding of the code's purpose and provides contextually relevant
      feedback."
  ]
}
```
"""  # noqa: E501

INSTRUCTIONS_TEMPLATE = """
The generated_workflow_dir is {{ generated_workflow_dir }}.
1. List files in the {{ generated_workflow_dir }} directory.
2. Check the file {{ generated_workflow_dir }}/agent.py.
3. Generate a comprehensive JSON evaluation file for the given agent.py script.

Analyze the agent's task, tools, and expected workflow to create thorough evaluation criteria.

## Evaluation Categories to Cover
{{ evaluation_categories }}

## Example of agent.py script and corresponding JSON evaluation file
{{ agent_script_and_json_example }}

"""  # noqa: E501


def get_instructions(generated_workflow_dir: str) -> str:
    """Get evaluation instructions with the generated_workflow_dir properly set."""
    template = Template(INSTRUCTIONS_TEMPLATE)
    return template.render(
        generated_workflow_dir=generated_workflow_dir,
        evaluation_categories=EVALUATION_CATEGORIES,
        agent_script_and_json_example=AGENT_SCRIPT_AND_JSON_EXAMPLE,
    )
