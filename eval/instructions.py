"""Instructions for the agent evaluation JSON generator.
The structured JSON output is saved as JSON format.
"""

from jinja2 import Template

WEBPAGE_DESCRIPTIONS = {
    "https://mozilla-ai.github.io/any-agent/tracing/": (
        "Useful for debugging and monitoring agent behavior with OpenTelemetry traces."
        "This page shows how to capture, visualize, "
        "and analyze agent execution traces for better insights."
    ),
    "https://mozilla-ai.github.io/any-agent/evaluation/": (
        "Consult when implementing evaluation for your agent systems."
        "This page provides a trace-first approach to evaluate"
        "agent performance against custom criteria using LLM-as-a-judge techniques."
    ),
}

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
# Example imports for the agent.py file:
from any_agent import AnyAgent, AgentConfig, AgentFramework
from any_agent.config import MCPStdio
from tools.review_code_with_llm import review_code_with_llm
from tools.search_tavily import search_tavily
from pydantic import BaseModel, Field

# Imports for environment variables
import os
from dotenv import load_dotenv
load_dotenv()

# Pydantic model for structured output
class CodeReviewOutput(BaseModel):
    code: str = Field(..., description="The code to be reviewed.")
    review: str = Field(..., description="The review of the code.")

# Example Single Agent syntax:
agent = AnyAgent.create(
    # agent framework name (1st positional arg)
    "openai",
    # agent configuration (2nd positional arg)
    AgentConfig(
        model_id="gpt-4.1",
        instructions="Example instructions",
        tools=[
            search_tavily, # Example tool taken from tools/README.md
            review_code_with_llm, # Example tool taken from tools/README.md
            # Example of MCP server usage
            MCPStdio(
                    command="docker",
                    # args taken verbatim from available_mcps.md
                    args=[
                        "run",
                        "-i",
                        "--rm",
                        "-e",
                        "BRAVE_API_KEY",
                        "mcp/brave-search",
                    ],
                    # Specify necessary environment variables
                    env={
                        "BRAVE_API_KEY": os.getenv("BRAVE_API_KEY"),
                    },
                    # From among the tools available from the MCP server
                    # list only the tools that are necessary for the solving the task at hand
                    tools=[
                        "brave_web_search",
                    ],
            ),
        ],
        output_type=CodeReviewOutput,
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
      "Ensure that the agent called search_tavily or another search tool to find relevant information about code review best practices or specific technologies mentioned in the code",
      "Ensure that the agent called review_code_with_llm to perform the actual code analysis and review",
      "Verify that the agent correctly identified the programming language and framework/libraries used in the provided code",
      "Check that the agent's review covers multiple aspects such as code quality, security, performance, and best practices",
      "Ensure that the agent searched for current standards or documentation related to the specific technologies or patterns found in the code",
      "Verify that the agent's output follows the required CodeReviewOutput structure with both 'code' and 'review' fields properly populated",
      "Check that the review includes specific, actionable recommendations for code improvement",
      "Ensure that the agent appropriately utilized the available MCP tools (brave_web_search) when additional context or verification was needed",
      "Verify that the final review demonstrates understanding of the code's purpose and provides contextually relevant feedback"
    }
  ]
}
```

Always use openai/gpt-4.1 as the llm_judge.

"""  # noqa: E501

INSTRUCTIONS_TEMPLATE = """
The generated_workflow_dir is {{ generated_workflow_dir }}.
1. List files in the {{ generated_workflow_dir }} directory.
2. Check the file {{ generated_workflow_dir }}/agent.py.
3. Generate a comprehensive JSON evaluation file for the given agent.py script.

Analyze the agent's task, tools, and expected workflow to create thorough evaluation criteria.

## Evaluation Categories to Cover
{{ evaluation_categories }}

You may access to the following webpages using `visit_webpage` tool:

{% for url, description in webpage_descriptions.items() %}
- {{ url }}: {{ description }}
{% endfor %}

## Example of agent.py script and corresponding JSON evaluation file

{{ agent_script_and_json_example }}

"""  # noqa: E501


def get_instructions(generated_workflow_dir: str) -> str:
    """Get evaluation instructions with the generated_workflow_dir properly set."""
    template = Template(INSTRUCTIONS_TEMPLATE)
    return template.render(
        generated_workflow_dir=generated_workflow_dir,
        webpage_descriptions=WEBPAGE_DESCRIPTIONS,
        evaluation_categories=EVALUATION_CATEGORIES,
        agent_script_and_json_example=AGENT_SCRIPT_AND_JSON_EXAMPLE,
    )
