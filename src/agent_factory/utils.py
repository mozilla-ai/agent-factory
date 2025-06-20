import json
from pathlib import Path

from agent_factory.prompt import UserPrompt
from agent_factory.schema import AgentFactoryOutputs


def remove_markdown_code_block_delimiters(text: str) -> str:
    """Remove backticks from the start and end of markdown output."""
    text = text.strip()
    if text.startswith("```") and text.endswith("```"):
        lines = text.splitlines()
        return "\n".join(lines[1:-1])
    return text


def validate_agent_outputs(str_output: str):
    try:
        str_output = remove_markdown_code_block_delimiters(str_output)
        json_output = json.loads(str_output)
        agent_factory_outputs = AgentFactoryOutputs.model_validate(json_output)
    except Exception as e:
        raise ValueError(
            f"Invalid format received for agent outputs: {e}. Could not parse the output as AgentFactoryOutputs."
        ) from e
    return agent_factory_outputs


def save_agent_parsed_outputs(output: AgentFactoryOutputs, output_dir: Path):
    """Save all three outputs from AgentFactoryOutputs to separate files."""
    agent_path = Path(f"{output_dir}/agent.py")
    instructions_path = Path(f"{output_dir}/INSTRUCTIONS.md")
    requirements_path = Path(f"{output_dir}/requirements.txt")

    with agent_path.open("w", encoding="utf-8") as f:
        f.write(remove_markdown_code_block_delimiters(output.agent_code))

    with instructions_path.open("w", encoding="utf-8") as f:
        f.write(output.run_instructions)

    with requirements_path.open("w", encoding="utf-8") as f:
        f.write(remove_markdown_code_block_delimiters(output.dependencies))

    print(f"Files saved to {output_dir}")


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
