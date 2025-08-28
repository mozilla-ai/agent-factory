import asyncio
import json
from pathlib import Path

import dotenv
import fire
from any_agent import AgentConfig, AgentFramework, AnyAgent
from eval.instructions import get_instructions
from eval.mcpd_tools import create_filesystem_tools, create_server_tools
from pydantic import BaseModel, Field

from agent_factory.tools.search_tavily import search_tavily
from agent_factory.tools.visit_webpage import visit_webpage

dotenv.load_dotenv()


class CostInfo(BaseModel):
    input_cost: float
    output_cost: float
    total_cost: float


class JSONEvaluationCase(BaseModel):
    criteria: list[str] = Field(default_factory=list, description="A list of evaluation criteria.")
    evaluation_case_generation_costs: CostInfo = Field(
        default_factory=lambda: CostInfo(input_cost=0.0, output_cost=0.0, total_cost=0.0),
        description="Costs for generating the evaluation case",
    )


async def main(
    generated_workflow_dir: str = "generated_workflows/latest",
    framework: AgentFramework = AgentFramework.OPENAI,
    model: str = "gpt-4.1",
    mcpd_url: str = "http://localhost:8090",
    use_dynamic_discovery: bool = False,
):
    """Generate JSON structured evaluation case for the generated agentic workflow.
    Save the JSON file as `evaluation_case.json` in the same directory as the generated workflow.

    Args:
        generated_workflow_dir: The directory of the generated workflow.
        framework (str): The agent framework to use
        model (str): The model ID to use
        mcpd_url (str): The URL of the mcpd daemon
        use_dynamic_discovery (bool): Whether to dynamically discover tools from mcpd
    """
    repo_root = Path.cwd()
    workflows_dir = repo_root / generated_workflow_dir

    # Use dynamic discovery if enabled, otherwise fall back to static
    if use_dynamic_discovery:
        try:
            filesystem_tools = await create_server_tools(
                "filesystem", 
                ["read_file", "list_directory"], 
                mcpd_url
            )
            if not filesystem_tools:
                print("Warning: Dynamic discovery returned no tools, falling back to static")
                filesystem_tools = create_filesystem_tools(mcpd_url)
        except Exception as e:
            print(f"Error with dynamic discovery: {e}, falling back to static tools")
            filesystem_tools = create_filesystem_tools(mcpd_url)
    else:
        filesystem_tools = create_filesystem_tools(mcpd_url)
    
    agent = AnyAgent.create(
        agent_framework=framework,
        agent_config=AgentConfig(
            model_id=model,
            instructions=get_instructions(generated_workflow_dir),
            tools=[
                visit_webpage,
                search_tavily,
                *filesystem_tools,
            ],
            output_type=JSONEvaluationCase,
        ),
    )

    run_instructions = """
    Read the {generated_workflow_dir}/agent.py script and generate a JSON evaluation case for it.
    The criteria generated must:
    - be specific, measurable, and independent.
    - should not be vague or open-ended or generic.
    - begin with phrases such as "Ensure that the agent..." or "Verify that the agent..." or "Check that the agent...".
    - be solely based on the agent's INSTRUCTIONS, tools in the agent configuration (including MCPs) and output_type JSON structured output.
    You may ignore the framework name and model_id in the agent configuration.
    """  # noqa: E501
    agent_trace = agent.run(run_instructions.format(generated_workflow_dir=generated_workflow_dir), max_turns=30)

    cost_info = agent_trace.cost
    evaluation_case_generation_costs = {
        "input_cost": cost_info.input_cost,
        "output_cost": cost_info.output_cost,
        "total_cost": cost_info.total_cost,
    }

    if not isinstance(agent_trace.final_output, JSONEvaluationCase):
        raise ValueError("The agent's final output is not a JSONEvaluationCase.")

    evaluation_case_data = agent_trace.final_output.model_dump()
    evaluation_case_data["evaluation_case_generation_costs"] = evaluation_case_generation_costs

    with (workflows_dir / "evaluation_case.json").open("w") as f:
        f.write(json.dumps(evaluation_case_data, indent=2))


def sync_main(**kwargs):
    """Synchronous wrapper for fire.Fire compatibility."""
    return asyncio.run(main(**kwargs))


if __name__ == "__main__":
    fire.Fire(sync_main)
