"""Instructions for the agent code generator."""

from importlib.metadata import version

from jinja2 import Template

ANY_AGENT_VERSION = version("any_agent")

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

AMENDMENT_PROMPT = """
Amend the Python code you generated for the agentic workflow to do the following:
{0}

If necessary, {1}
"""

CODE_EXAMPLE_WITH_COMMENTS = """
# agent.py

# good to have
import os

# ALWAYS used
from dotenv import load_dotenv
from any_agent import AgentConfig, AnyAgent
from pydantic import BaseModel, Field
from fire import Fire

# MCPStdio should be imported ONLY if MCP servers are used in AgentConfig
from any_agent.config import MCPStdio

# ADD BELOW HERE: tools made available by any-agent or agent-factory
from any_agent.tools import visit_webpage
from tools.translate_text_with_llm import translate_text_with_llm

load_dotenv()


# ========= Structured output definition =========
class StructuredOutput(BaseModel):
    url: str = Field(..., description="The URL of the webpage that was translated.")
    source_language: str = Field(..., description="The source language detected on the webpage (should be 'English').")
    extracted_text: str = Field(..., description="The main text content extracted from the original English webpage.")
    translated_text: str = Field(..., description="The English text translated to Italian.")


# ========= System Instructions =========
INSTRUCTIONS = '''
You are an assistant that translates the main text content of an English webpage to Italian, following this step-by-step workflow:
1. Receive a webpage URL from the user. Visit the page and extract the primary and most relevant English text content. Focus on body content, main text, and important sections. Exclude navigation bars, headings not part of the content, footers, advertisements, and non-informational elements. Make sure the extracted text is concise but comprehensive and represents the actual page content.
2. Identify and confirm that the detected source language is English. If the page is not in English, halt and output the detected language and a clear message in 'translated_text'.
3. Use the translation tool to translate the extracted English text into fluent Italian.
4. Your output must be a structured JSON object with these fields:
   - url: the provided webpage URL
   - source_language: the detected primary language (should be English)
   - extracted_text: the main English content you extracted
   - translated_text: your Italian translation of the extracted text
Limit the output to 1000 tokens if the page is very long. Ensure the translation is accurate and clear. Do not make up or hallucinate content.
'''


TOOLS = [
    visit_webpage,                # To fetch and extract page text
    translate_text_with_llm,      # To translate extracted text
    MCPStdio(                     # To search results on the web
        command="docker",
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
]


agent = AnyAgent.create(
    "openai",
    AgentConfig(
        model_id="o3",
        instructions=INSTRUCTIONS,
        tools=TOOLS,
        output_type=StructuredOutput,
    ),
)


def run_agent(url: str):
    \"\"\"
    Given a webpage URL, translate its main English content to Italian,
    and return structured output.
    \"\"\"
    input_prompt = f"Translate the main text content from the following English webpage URL to Italian: {url}"
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
"""  # noqa: E501

DELIVERABLES_INSTRUCTIONS = f"""
# Instructions to generate final deliverables

The final expected output is a dictionary with the following structure:

{{
    "agent_instructions": "The instructions passed to the generated agent.",
    "tools": "The python code that defines the tools to be used by the generated agent.",
    "imports": "The python code snippet needed to import the required tools.",
    "structured_outputs": "The Pydantic v2 models used to structure the agent's final output.",
    "cli_args": "The arguments to be provided to the agent from the command line.",
    "agent_description": "The description of the agent and what it does.",
    "prompt_template": "A prompt template that, completed with cli_args, defines the agent's input prompt.",
    "run_instructions": "The instructions for setting up the environment in Markdown format.",
    "dependencies": "The list of python dependencies in Markdown format."
}}

## Values to assign to dictionary keys

1. `agent_instructions` is a string that will be assigned to the `INSTRUCTIONS` variable in the template (type: str).
This string replaces the {{agent_instructions}} placeholder in the agent code template.
2. `tools` is python code that assigns the `TOOLS` variable with the list of tools required by the generated agent. This code replaces the {{tools}} placeholder in the agent code template.
3. `imports` is python code containing all the required imports for the selected tools. This code replaces the {{imports}} placeholder in the agent code template.
4. `structured_outputs` is python code that defines the class `StructuredOutput(BaseModel)`) defining the agent's output schema as a Pydantic v2 model.
This code replaces the {{structured_outputs}} placeholder in the agent code template.
5. `cli_args` are the arguments to be passed to the `run_agent` function. Each of them is specified as argument_name: argument_value.
These will replace the {{cli_args}} placeholder in the agent code template.
6. `agent_description` is a string to be provided as the description of the `run_agent` function.
7. `prompt_template` is an f-string which is formatted with the values of `cli_args` to build the final input prompt to the generated agent.
8. `run_instructions` should contain clear and concise setup instructions:
    - Environment variables: Instruct the user to create a .env file to set environment variables; specify exactly which environment variables are required
    - Always include the following instructions to install Python package manager uv (the end user decides which command to run based on their OS):
        - for MacOS and Linux users: `curl -LsSf https://astral.sh/uv/install.sh | sh`
        - for Windows users: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
    - Run instructions for agent.py using `uv run` with specification of requirements.txt and Python 3.11
      `uv run --with-requirements generated_workflows/latest/requirements.txt --python 3.11 python generated_workflows/latest/agent.py --arg1 "value1"`
9. dependencies should list all the python libraries (including the ones required by the tools) as dependencies to be installed. It will be used to generate the requirements.txt file
    - the first line should be "any-agent[all]=={ANY_AGENT_VERSION}" dependency, since we are using any-agent to run the agent workflow
    - only if the `agent_code` uses `uvx` to spin up any MCP server, include "uv" as a dependency in the requirements.txt file
"""  # noqa: E501

AGENT_CODE_TEMPLATE = """
# agent.py

# good to have
import os

# ALWAYS used
from dotenv import load_dotenv
from any_agent import AgentConfig, AnyAgent, AgentRunError
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


CODE_GENERATION_INSTRUCTIONS = f"""
# Single Agent Implementation with Multiple Steps

## Task Overview
Create a complete implementation of a single agent that executes a multi-step workflow
using Mozilla's any-agent library. The implementation should:

1. Use the OpenAI framework as the underlying agent provider
2. Implement a step-by-step approach where the agent breaks down the user's request into multiple steps, each with an input and output
3. To obtain JSON output from the agent, define structured output using Pydantic v2 models via the output_type argument
4. Whenever required, assign tools in the agent configuration.

## Required Components

#### Model (model_id):
- Use o3 as the model_id

#### Instructions (instructions):
- Decide on the number of steps that you think would be necessary to complete the task
- Keep the number of steps to a minimum
- Provide a step-by-step clear multi-step system instructions that guides the agent's behavior
- The instructions should be as detailed and as unambiguous as possible
- Define the instructions in an INSTRUCTIONS variable that will be passed to AgentConfig

#### Tools (tools):
- Suggest list of tools that you think would be necessary to complete the steps to be used in the agent configuration AgentConfig(tools=[...]).
  Try to use only the minimum subset of tools that are necessary for the solving the task at hand.
- You must choose tools from the following 3 categories, *listed in order of priority* (i.e. tools found in an earlier category are preferable to equivalent tools found in following ones):
    a. Python Functions: The available tools are described in the local file at tools/available_tools.md - which can be read using `read_file` tool.
       Each tool in available_tools.md has a corresponding .py file in the tools/ directory that implements the function.
    b. Tools pre-defined in any-agent library: `search_tavily` and `visit_webpage` tools
    c. MCP Servers: To discover a relevant MCP server, first use the `search_mcp_servers` tool,
       giving it a keyword that describes the task you want to accomplish.
       Then, read each MCP server's description carefully to verify which one provides the tools you need for the task.
       Each MCP has a configuration that must be accurately implemented in the agent configuration via MCPStdio().
       Always suggest only the minimum subset of tools from the MCP server URL that are necessary for the solving the task at hand.
       If the agent is required to generate any intermediate files, you may ask it to save them in a path relative to the current working directory (do not give absolute paths).
       You must never import or assign `search_mcp_servers` to the tools list of the generated agent in `agent_code`.

#### Structured Output (output_type):
- Define Pydantic v2 models to structure the agent's final output
- Implement the output_type argument correctly to obtain this structured response

#### Agent Trace (agent_trace):
The code implementation should include the agent trace being saved into a JSON file named `agent_eval_trace.json` immediately after agent.run()
- Saving of the agent trace in the code should be done to the `generated_workflows/latest/` directory. You may assume that the `generated_workflows/latest/` directory already exists
- You would accomplish this by including the lines agent_trace.model_dump_json(indent=2) as shown in the example code
- Never try to print, log or access any other properties of the agent trace object. agent_trace.response or agent_trace.output are invalid
- Only agent_trace.model_dump_json(indent=2) and agent_trace.final_output are valid
- Do not print or save anything after saving the agent trace

### Code Organization
- Create well-documented, modular code with appropriate comments
- Follow Python best practices for readability and maintainability
- Include proper import statements and dependency management
- Environment variables required by the code/tools/MCP servers can be assumed to be set in the .env file:
    - Use Python dotenv library to load the environment variables and access them using os.getenv()

### Agent code template

- Rely on the following template to write the agent code:

```
{AGENT_CODE_TEMPLATE}
```
"""  # noqa: E501

# Define the template with Jinja2 syntax
INSTRUCTIONS_TEMPLATE = """
You are an expert software developer with a deep understanding of Mozilla AI's any-agent Python library.

Any-agent library enables you to:
- Build agent systems with a unified API regardless of the underlying framework
- Switch between different agent frameworks (like OpenAI, LangChain, smolagents) without rewriting code
- Create both single-agent and multi-agent systems with consistent patterns
- Leverage built-in tools like web search and webpage visiting as well as MCP servers
- Implement comprehensive tracing and evaluation capabilities

**Any-agent Code Generation Instructions**

{{ code_generation_instructions }}

As input to the AgentConfig, you are required to provide the parameters `model_id`, `instructions`, `tools`, and `output_type`.
You also need to specify the correct imports, which have to be consistent with the tools used by the agent:

{{ code_example_with_comments }}

** Deliverables Instructions**

{{ deliverables_instructions }}
"""  # noqa: E501

# Render the template
template = Template(INSTRUCTIONS_TEMPLATE)
INSTRUCTIONS = template.render(
    code_generation_instructions=CODE_GENERATION_INSTRUCTIONS,
    code_example_with_comments=CODE_EXAMPLE_WITH_COMMENTS,
    deliverables_instructions=DELIVERABLES_INSTRUCTIONS,
)
