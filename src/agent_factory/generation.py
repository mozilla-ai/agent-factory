import json
from pathlib import Path

import dotenv
import fire
from any_agent import AgentConfig, AgentFramework, AgentRunError, AnyAgent
from any_agent.tools import search_tavily, visit_webpage
from any_agent.tracing.agent_trace import AgentTrace

from agent.factory_tools import read_file, search_mcp_servers
from agent.instructions import AGENT_CODE_TEMPLATE, AGENT_CODE_TEMPLATE_RUN_VIA_CLI, load_system_instructions
from agent.schemas import AgentFactoryOutputs
from agent.utils.artifact_validation import clean_python_code_with_autoflake
from agent.utils.io_utils import setup_output_directory
from agent.utils.logging import logger
from agent_factory.prompt import UserPrompt

dotenv.load_dotenv()


def create_agent():
    framework = AgentFramework.OPENAI
    agent = AnyAgent.create(
        framework,
        AgentConfig(
            model_id="o3",
            instructions=load_system_instructions(for_cli_agent=True),
            tools=[visit_webpage, search_tavily, search_mcp_servers, read_file],
            output_type=AgentFactoryOutputs,
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


def run_agent(agent: AnyAgent, user_prompt: str, max_turns: int = 30) -> AgentTrace:
    try:
        return agent.run(user_prompt, max_turns=max_turns)
    except AgentRunError as e:
        logger.error(f"Agent execution failed: {e}")
        logger.warning("Retrieved partial agent trace...")
        return e.trace


def save_agent_outputs(agent_trace: AgentTrace, output_dir: Path) -> None:
    # Create enriched trace data with costs as separate metadata
    cost_info = agent_trace.cost
    input_cost = cost_info.input_cost
    output_cost = cost_info.output_cost
    total_cost = cost_info.total_cost
    trace_data = agent_trace.model_dump()
    trace_data["execution_costs"] = {"input_cost": input_cost, "output_cost": output_cost, "total_cost": total_cost}

    # Save the enriched trace
    trace_path = output_dir / "agent_factory_trace.json"
    with trace_path.open("w", encoding="utf-8") as f:
        f.write(json.dumps(trace_data, indent=2))

    if not hasattr(agent_trace, "final_output") or not agent_trace.final_output:
        raise RuntimeError("No final_output available in agent trace")

    try:
        agent_path = output_dir / "agent.py"
        readme_path = output_dir / "README.md"
        requirements_path = output_dir / "requirements.txt"
        agent_code = (
            f"{AGENT_CODE_TEMPLATE.format(**agent_trace.final_output.model_dump())} \n"
            f"{AGENT_CODE_TEMPLATE_RUN_VIA_CLI.format(**agent_trace.final_output.model_dump())}"
        )

        cleaned_agent_code = clean_python_code_with_autoflake(agent_code)

        with agent_path.open("w", encoding="utf-8") as f:
            f.write(cleaned_agent_code)

        with readme_path.open("w", encoding="utf-8") as f:
            f.write(agent_trace.final_output.readme)

        with requirements_path.open("w", encoding="utf-8") as f:
            f.write(agent_trace.final_output.dependencies)

        logger.info(f"Agent files saved to {output_dir}")

    except Exception as e:
        logger.warning(f"Warning: Failed to parse and save agent outputs: {str(e)}")


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
