import asyncio
import json
from pathlib import Path

import fire
from any_agent import AgentFramework, AgentTrace
from any_agent.evaluation import AgentJudge
from any_agent.evaluation.schemas import EvaluationOutput

from agent_factory.utils.logging import logger
from agent_factory.utils.trace_utils import load_agent_trace

from .generate_evaluation_case import JSONEvaluationCase


async def run_evaluation(
    generated_workflow_dir: str = "generated_workflows/latest",
    evaluation_case_json_file: str | None = None,
    agent_trace_json_file: str | None = None,
    save_evaluation_results_path: str | None = None,
    framework: AgentFramework = AgentFramework.TINYAGENT,
    model: str = "gpt-4.1",
):
    """Runs the evaluation process based on an evaluation case JSON file and an agent trace JSON file.

    Args:
        generated_workflow_dir (str): The directory of the generated workflow.
        Defaults to "generated_workflows/latest".

        evaluation_case_json_file (str, optional): Path to the evaluation case JSON file.
        If None, will use generated_workflow_dir/evaluation_case.json.

        agent_trace_json_file (str, optional): Path to the agent trace JSON file.
        If None, will use generated_workflow_dir/agent_eval_trace.json.

        save_evaluation_results_path (str, optional): Path to save the evaluation results JSON file.
        If None, will use generated_workflow_dir/evaluation_results.json.

        framework (str): The agent framework the Agent Judge should use.
        model (str): The model ID the Agent Judge should use.
    """
    # Set default paths based on generated_workflow_dir if not provided
    if evaluation_case_json_file is None:
        evaluation_case_json_file = f"{generated_workflow_dir}/evaluation_case.json"
    if agent_trace_json_file is None:
        agent_trace_json_file = f"{generated_workflow_dir}/agent_eval_trace.json"
    if save_evaluation_results_path is None:
        save_evaluation_results_path = f"{generated_workflow_dir}/evaluation_results.json"

    try:
        # Load evaluation case from the specified JSON file
        with Path(evaluation_case_json_file).open(encoding="utf-8") as f:
            evaluation_case = JSONEvaluationCase.model_validate_json(f.read())
        logger.info(f"Successfully loaded evaluation case from: {evaluation_case_json_file}")

        agent_trace = load_agent_trace(agent_trace_json_file)
        logger.info(f"Successfully loaded agent trace from: {agent_trace_json_file}")

        # Perform the evaluation
        agent_judge = AgentJudge(model_id=model, framework=framework)
        eval_traces = []
        runs = []
        for criteria in evaluation_case.criteria:
            runs.append(agent_judge.run_async(agent_trace, criteria))
        eval_traces: list[AgentTrace] = await asyncio.gather(*runs)
        results: list[EvaluationOutput] = [t.final_output for t in eval_traces]

        # Track costs from evaluation traces
        total_cost = 0.0

        for trace in eval_traces:
            total_cost += trace.cost.total_cost

        score = sum(result.passed for result in results)
        # Print the results
        logger.info("\n--- Evaluation Results ---")
        logger.info(f"Final score: {score} out of {len(evaluation_case.criteria)}")

        # Save evaluation results to a JSON file
        eval_result_dict = {
            "obtained_score": score,
            "max_score": len(evaluation_case.criteria),
            "results": [result.model_dump() for result in results],
            "total_cost": total_cost,
        }
        with Path(save_evaluation_results_path).open("w", encoding="utf-8") as f:
            f.write(json.dumps(eval_result_dict, indent=2))
            logger.info(f"Successfully saved evaluation results to: {save_evaluation_results_path}")

    except FileNotFoundError as e:
        logger.error(f"Error: File not found - {e.filename}")
        logger.error("Please ensure the specified file paths are correct.")
    except AttributeError as e:
        logger.error(
            "Error: An attribute was not found in the evaluation result objects. "
            f"This might indicate an unexpected structure for eval_result itself. Details: {e}"
        )
    except ValueError as e:
        logger.error(f"Error: Invalid evaluation result format. Details: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        logger.error("Evaluation could not be completed.")


if __name__ == "__main__":
    fire.Fire(run_evaluation)
