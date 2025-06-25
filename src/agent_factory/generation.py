import uuid
from datetime import datetime
from pathlib import Path

import dotenv
import fire
from any_agent import AgentConfig, AgentFramework, AgentRunError, AnyAgent
from any_agent.tools import search_tavily, visit_webpage
from any_agent.tracing.agent_trace import AgentTrace
from pydantic import BaseModel, Field

from agent_factory.instructions import AGENT_CODE_TEMPLATE, INSTRUCTIONS
from agent_factory.logging import logger
from agent_factory.prompt import UserPrompt
from agent_factory.tools import read_file, search_mcp_servers

dotenv.load_dotenv()

OUTPUT_DICTIONARY = {}


class AgentFactoryOutputs(BaseModel):
    agent_instructions: str = Field(..., description="The instructions passed to the generated agent.")
    tools: str = Field(..., description="The python code that defines the tools to be used by the generated agent.")
    imports: str = Field(..., description="The python code snippet used to import the required tools.")
    structured_outputs: str = Field(..., description="The Pydantic v2 models used to structure the agent's output.")
    cli_args: str = Field(..., description="The arguments to be provided to the agent from the command line.")
    agent_description: str = Field(..., description="The description of the agent and what it does.")
    prompt_template: str = Field(
        ..., description="A prompt template that, completed with cli_args, defines the agent's input prompt."
    )
    run_instructions: str = Field(..., description="The run instructions in Markdown format")
    dependencies: str = Field(..., description="The dependencies line by line in Markdown format")


def save_to_dictionary(
    agent_instructions: str,
    tools: str,
    imports: str,
    structured_outputs: str,
    cli_args: str,
    agent_description: str,
    prompt_template: str,
    run_instructions: str,
    dependencies: str,
) -> None:
    """Saves key/value pairs into the output dictionary.

    Parameters:
    - agent_instructions: The instructions passed to the generated agent
    - tools: The python code that defines the tools to be used by the generated agent
    - imports: The python code snippet needed to import the required tools
    - structured_outputs: The Pydantic v2 models used to structure the agent's final output
    - run_agent_code: The python code for the `run_agent` function, taking input parameters from
      the user and calling the agent
    - run_instructions: The instructions for setting up the environment in Markdown format
    - dependencies: The list of python dependencies in Markdown format
    """
    print("[i] Storing data into the dictionary")
    OUTPUT_DICTIONARY["agent_instructions"] = agent_instructions
    OUTPUT_DICTIONARY["tools"] = tools
    OUTPUT_DICTIONARY["imports"] = imports
    OUTPUT_DICTIONARY["structured_outputs"] = structured_outputs
    OUTPUT_DICTIONARY["cli_args"] = cli_args
    OUTPUT_DICTIONARY["agent_description"] = agent_description
    OUTPUT_DICTIONARY["prompt_template"] = prompt_template
    OUTPUT_DICTIONARY["run_instructions"] = run_instructions
    OUTPUT_DICTIONARY["dependencies"] = dependencies


def validate_agent_outputs():
    try:
        agent_factory_outputs = AgentFactoryOutputs.model_validate(OUTPUT_DICTIONARY)
    except Exception as e:
        raise ValueError(
            f"Invalid format received for agent outputs: {e}. Could not parse the output as AgentFactoryOutputs."
        ) from e
    return agent_factory_outputs


def remove_markdown_code_block_delimiters(text: str) -> str:
    """Remove backticks from the start and end of markdown output."""
    text = text.strip()
    if text.startswith("```") and text.endswith("```"):
        lines = text.splitlines()
        return "\n".join(lines[1:-1])
    return text


def save_agent_parsed_outputs(output: AgentFactoryOutputs, output_dir: Path):
    """Save outputs from AgentFactoryOutputs to separate files."""
    agent_path = Path(f"{output_dir}/agent.py")
    instructions_path = Path(f"{output_dir}/INSTRUCTIONS.md")
    requirements_path = Path(f"{output_dir}/requirements.txt")

    # build agent code from dict keys + template
    agent_code = AGENT_CODE_TEMPLATE.format(**OUTPUT_DICTIONARY)

    # save the agent code
    with agent_path.open("w", encoding="utf-8") as f:
        f.write(remove_markdown_code_block_delimiters(agent_code))

    with instructions_path.open("w", encoding="utf-8") as f:
        f.write(output.run_instructions)

    with requirements_path.open("w", encoding="utf-8") as f:
        f.write(remove_markdown_code_block_delimiters(output.dependencies))

    logger.info(f"Files saved to {output_dir}")


def create_agent():
    framework = AgentFramework.OPENAI
    agent = AnyAgent.create(
        framework,
        AgentConfig(
            model_id="o3",
            instructions=INSTRUCTIONS,
            tools=[visit_webpage, search_tavily, search_mcp_servers, read_file, save_to_dictionary],
            model_args={"tool_choice": "required"},  # Ensure tool choice is required
        ),
    )
    return agent


def build_run_instructions(user_prompt) -> str:
    """Build the run instructions for the agent based on the user prompt.

    Build the run instructions for the agent based on the user prompt.
    If a UserPrompt instance already exists, a task has alredy been assigned to the agent.
    Thus, we amend the existing prompt with the new user instructions.
    If no UserPrompt instance exists, we create a new one with the user prompt.

    Args:
        user_prompt (str): The user prompt to build the run instructions from.

    Returns:
        str: The run instructions for the agent.
    """
    if UserPrompt._instance is None:
        user_prompt_instance = UserPrompt(user_prompt)
        return user_prompt_instance.get_prompt()
    else:
        user_prompt_instance = UserPrompt._instance
        return user_prompt_instance.amend_prompt(user_prompt)


def setup_output_directory(output_dir: Path | None = None) -> Path:
    if output_dir is None:
        output_dir = Path.cwd()
        uid = datetime.now().strftime("%Y-%m-%d_%H:%M:%S") + "_" + str(uuid.uuid4())[:8]
        # store in a unique dir under generated_workflows by default
        output_dir = output_dir / "generated_workflows" / uid
    else:
        # guarantee output_dir is PosixPath
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def run_agent(agent: AnyAgent, user_prompt: str, max_turns: int = 30) -> AgentTrace:
    try:
        return agent.run(user_prompt, max_turns=max_turns)
    except AgentRunError as e:
        print(f"Agent execution failed: {e}")
        print("Retrieved partial agent trace...")
        return e.trace


def save_agent_outputs(agent_trace: AgentTrace, output_dir: Path) -> None:
    trace_path = output_dir / "agent_factory_trace.json"
    trace_path.write_text(agent_trace.model_dump_json(indent=2))

    if not hasattr(agent_trace, "final_output") or not agent_trace.final_output:
        raise RuntimeError("No final_output available in agent trace")

    try:
        agent_outputs = validate_agent_outputs()
        save_agent_parsed_outputs(agent_outputs, output_dir)
    except Exception as e:
        print(f"Warning: Failed to parse agent's structured outputs: {str(e)}")


def single_turn_generation(
    user_prompt: str,
    output_dir: Path | None = None,
    max_turns: int = 30,
) -> None:
    """Generate python code for an agentic workflow based on the user prompt.

    Args:
        user_prompt: The user's prompt describing the desired agent behavior.
        output_dir: Optional directory to save outputs to. If None, creates a unique directory.
    """
    output_dir = setup_output_directory(output_dir)

    agent = create_agent()
    run_instructions = build_run_instructions(user_prompt)

    agent_trace = run_agent(agent, run_instructions, max_turns=max_turns)
    save_agent_outputs(agent_trace, output_dir)
    logger.info(f"Workflow files saved in: {output_dir}")


def main():
    fire.Fire(single_turn_generation)


if __name__ == "__main__":
    main()
