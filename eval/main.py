import logging
import re
from pathlib import Path

import dotenv
import fire
import yaml
from any_agent import AgentConfig, AgentFramework, AnyAgent
from any_agent.config import MCPStdio
from any_agent.tools import search_tavily, visit_webpage
from eval.instructions import INSTRUCTIONS
from pydantic import BaseModel, Field, ValidationError

dotenv.load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class CheckpointCriteria(BaseModel):
    criteria: str = Field(..., description="The criteria for the checkpoint.")
    points: int = Field(..., description="The points for the checkpoint.")


class JSONEvaluationCase(BaseModel):
    llm_judge: str = Field(default="openai/gpt-4.1", description="The LLM to be used as the judge.")
    checkpoints: list[CheckpointCriteria] = Field(
        ..., description="The checkpoints criteria to be used for evaluation."
    )


def parse_checkpoint_criteria_string(input_string: str) -> dict:
    """Hacky solution to go from agent_trace.final_output (string) to JSON.
    TODO: Check with any-agent team to see if this can be fixed in the library's tracing.
    """
    result_dict = {"llm_judge": None, "checkpoints": []}

    # 1. Extract llm_judge
    llm_judge_match = re.search(r"llm_judge='([^']+)'", input_string)
    if llm_judge_match:
        result_dict["llm_judge"] = llm_judge_match.group(1)

    # 2. Extract and parse checkpoints
    checkpoints_str_match = re.search(r"checkpoints=\[(.*)\]", input_string)
    if checkpoints_str_match:
        checkpoints_content = checkpoints_str_match.group(1)
        checkpoint_matches = re.findall(
            r"CheckpointCriteria\(criteria='((?:[^']|\\')*)', points=(\d+)\)", checkpoints_content
        )
        for criteria, points in checkpoint_matches:
            criteria = criteria.replace("\\'", "'")
            try:
                result_dict["checkpoints"].append({"criteria": criteria, "points": int(points)})
            except ValueError:
                print(f"Warning: Could not parse points for criteria: '{criteria}', points_str: '{points}'")
                continue

    return result_dict


def main(generated_workflow_dir: str = "generated_workflows/latest"):
    """Generate JSON structured evaluation case for the generated agentic workflow.
    Save the JSON file as `evaluation_case.yaml` in the same directory as the generated workflow.

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

    # Save the agent trace as a YAML file
    json_output = parse_checkpoint_criteria_string(agent_trace.final_output)

    try:
        json_output = JSONEvaluationCase.model_validate(json_output)
    except ValidationError as e:
        logger.error("Invalid JSON output: %s", e)
        return

    # Save the JSON output as a YAML file
    with (workflows_dir / "evaluation_case.yaml").open("w") as f:
        yaml.dump(json_output.model_dump(), f, default_flow_style=False, sort_keys=False)


if __name__ == "__main__":
    fire.Fire(main)
