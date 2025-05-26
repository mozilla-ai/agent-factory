"""Instructions for the agent evaluation JSON generator.
The structured JSON output is later saved as YAML programatically.
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

SCORING_GUIDELINES = """
- **Total points**: 8-15 points across all criteria
- **Tool calls**: 1-2 points per essential tool usage
- **Data processing**: 1-2 points for calculations/combinations
- **Final output**: 1-2 points for answer quality
Make criteria **specific**, **measurable**, and **independent**
"""

AGENT_SCRIPT_AND_JSON_EXAMPLE = """

**Agent Script:**
```python
# Example imports for the agent.py file:
from any_agent import AnyAgent, AgentConfig, AgentFramework, TracingConfig
from any_agent.tools import search_web, visit_webpage
from any_agent.config import MCPStdio
from tools.review_code_with_llm import review_code_with_llm
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
            search_web, # Example tool available from any-agent library
            review_code_with_llm, # Example tool taken from tools/available_tools.md
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
        agent_args={
            "output_type": CodeReviewOutput
        }
    ),
)

# Running the agent
user_input = "Example user input code to be reviewed"
agent.run(prompt=user_input)

```

**Generated JSON:**
```json
{
  "llm_judge": "openai/gpt-4.1",
  "checkpoints": [
    {
      "points": 2,
      "criteria": "Ensure that the agent called search_web or brave_web_search to find relevant information about code review best practices or specific technologies mentioned in the code"
    },
    {
      "points": 2,
      "criteria": "Ensure that the agent called review_code_with_llm to perform the actual code analysis and review"
    },
    {
      "points": 1,
      "criteria": "Verify that the agent correctly identified the programming language and framework/libraries used in the provided code"
    },
    {
      "points": 2,
      "criteria": "Check that the agent's review covers multiple aspects such as code quality, security, performance, and best practices"
    },
    {
      "points": 1,
      "criteria": "Ensure that the agent searched for current standards or documentation related to the specific technologies or patterns found in the code"
    },
    {
      "points": 2,
      "criteria": "Verify that the agent's output follows the required CodeReviewOutput structure with both 'code' and 'review' fields properly populated"
    },
    {
      "points": 1,
      "criteria": "Check that the review includes specific, actionable recommendations for code improvement"
    },
    {
      "points": 1,
      "criteria": "Ensure that the agent appropriately utilized the available MCP tools (brave_web_search) when additional context or verification was needed"
    },
    {
      "points": 1,
      "criteria": "Verify that the final review demonstrates understanding of the code's purpose and provides contextually relevant feedback"
    }
  ]
}
```

Always use openai/gpt-4.1 as the llm_judge.

"""  # noqa: E501

INSTRUCTIONS_TEMPLATE = """
Generate a comprehensive JSON evaluation file for the given agent.py script.
Analyze the agent's task, tools, and expected workflow to create thorough evaluation criteria.

## Evaluation Categories to Cover
{{ evaluation_categories }}

## Scoring Guidelines
{{ scoring_guidelines }}

You may access to the following webpages using `visit_webpage` tool:

{% for url, description in webpage_descriptions.items() %}
- {{ url }}: {{ description }}
{% endfor %}

## Example of agent.py script and corresponding JSON evaluation file

{{ agent_script_and_json_example }}

"""  # noqa: E501

# Render the template with the WEBPAGE_DESCRIPTIONS dictionary
template = Template(INSTRUCTIONS_TEMPLATE)
INSTRUCTIONS = template.render(
    webpage_descriptions=WEBPAGE_DESCRIPTIONS,
    evaluation_categories=EVALUATION_CATEGORIES,
    scoring_guidelines=SCORING_GUIDELINES,
    agent_script_and_json_example=AGENT_SCRIPT_AND_JSON_EXAMPLE,
)
