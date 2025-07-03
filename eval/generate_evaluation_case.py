import json
from pathlib import Path

import dotenv
import fire
from any_agent import AgentConfig, AgentFramework, AnyAgent
from any_agent.config import MCPStdio
from any_agent.tools import search_tavily, visit_webpage
from pydantic import BaseModel, Field

from eval.instructions import INSTRUCTIONS

dotenv.load_dotenv()


class JSONEvaluationCase(BaseModel):
    criteria: list[str] = Field(default_factory=list, description="A list of evaluation criteria.")


def main(generated_workflow_dir: str = "generated_workflows/latest"):
    """Generate JSON structured evaluation case for the generated agentic workflow.
    Save the JSON file as `evaluation_case.json` in the same directory as the generated workflow.

    Args:
        generated_workflow_dir: The directory of the generated workflow.

    """
    repo_root = Path.cwd()
    workflows_dir = repo_root / generated_workflow_dir

    # Create a separate directory for file operations
    file_ops_dir = "/app"
    mount_workflows_dir = f"/app/{generated_workflow_dir}"

    framework = AgentFramework.OPENAI
    agent = AnyAgent.create(
        framework,
        AgentConfig(
            model_id="gpt-4.1",
            instructions=INSTRUCTIONS,
            tools=[
                visit_webpage,
                search_tavily,
                MCPStdio(
                    command="docker",
                    args=[
                        "run",
                        "-i",
                        "--rm",
                        "--volume",
                        "/app",
                        # Mount workflows directory
                        "--mount",
                        f"type=bind,src={workflows_dir},dst={mount_workflows_dir}",
                        "mcp/filesystem",
                        file_ops_dir,
                    ],
                    tools=[
                        "read_file",
                        "list_directory",
                    ],
                ),
            ],
            output_type=JSONEvaluationCase,
        ),
    )

    run_instructions = """
    Read the generated_workflows/latest/agent.py script and generate a JSON evaluation case for it.
    The criteria generated must:
    - be specific, measurable, and independent.
    - should not be vague or open-ended or generic.
    - begin with phrases such as "Ensure that the agent..." or "Verify that the agent..." or "Check that the agent...".
    - be solely based on the agent's INSTRUCTIONS, tools in the agent configuration (including MCPs) and output_type JSON structured output.
    You may ignore the framework name and model_id in the agent configuration.
    """  # noqa: E501
    agent_trace = agent.run(run_instructions, max_turns=30)

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


if __name__ == "__main__":
    fire.Fire(main)
