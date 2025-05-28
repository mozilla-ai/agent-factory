from pathlib import Path

import fire
from any_agent.evaluation.evaluate import evaluate
from any_agent.evaluation.evaluation_case import EvaluationCase
from any_agent.tracing.agent_trace import AgentTrace


def run_evaluation(
    evaluation_case_yaml_file: str = "generated_workflows/evaluation_case.yaml",
    agent_trace_json_file: str = "generated_workflows/agent_trace.json",
):
    """Runs the evaluation process based on an evaluation case YAML file and an agent trace JSON file.

    Args:
        evaluation_case_yaml_file (str): Path to the evaluation case YAML file.
                                         Defaults to "generated_workflows/evaluation_case.yaml".
        agent_trace_json_file (str): Path to the agent trace JSON file.
                                     Defaults to "generated_workflows/agent_trace.json".
    """
    try:
        # Load evaluation case from the specified YAML file
        evaluation_case = EvaluationCase.from_yaml(evaluation_case_yaml_file)
        print(f"Successfully loaded evaluation case from: {evaluation_case_yaml_file}")

        # Load agent trace from the specified JSON file
        with Path(agent_trace_json_file).open(encoding="utf-8") as f:
            agent_trace_data = f.read()
            agent_trace = AgentTrace.model_validate_json(agent_trace_data)
        print(f"Successfully loaded agent trace from: {agent_trace_json_file}")

        # Perform the evaluation
        eval_result = evaluate(
            evaluation_case=evaluation_case,
            trace=agent_trace,
        )

        # Print the results
        print("\n--- Evaluation Results ---")
        print(f"Final score: {eval_result.score}")

        if eval_result.checkpoint_results:
            print("Checkpoint results:")
            for i, cp_result in enumerate(eval_result.checkpoint_results):
                print(f"\tCheckpoint {i + 1}:")
                print(f"\t\tCriteria: {cp_result.criteria}")
                print(f"\t\tCriteria Points: {cp_result.points}")
                print(f"\t\tPassed: {cp_result.passed}")
                print(f"\t\tReason: {cp_result.reason}")
        else:
            print("No checkpoint results available.")

    except FileNotFoundError as e:
        print(f"Error: File not found - {e.filename}")
        print("Please ensure the specified file paths are correct.")
    except AttributeError:
        print(
            "Error: An attribute was not found in the evaluation result objects. "
            "This might indicate an unexpected structure for eval_result itself. Details: {e}"
        )
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        print("Evaluation could not be completed.")


if __name__ == "__main__":
    fire.Fire(run_evaluation)
