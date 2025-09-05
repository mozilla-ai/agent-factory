import asyncio
from unittest import mock

from agent_factory.eval.run_generated_agent_evaluation import run_evaluation


def test_evaluation_runs_with_valid_inputs(tmpdir, sample_evaluation_json_file, sample_agent_eval_trace_json):
    """Tests that the evaluation script runs successfully with mock data."""
    evaluation_case_path = tmpdir.join("evaluation_case.json")
    evaluation_case_path.write(sample_evaluation_json_file)

    agent_trace_path = tmpdir.join("agent_eval_trace.json")
    agent_trace_path.write(sample_agent_eval_trace_json)

    results_path = tmpdir.join("evaluation_results.json")

    with mock.patch("builtins.print"):
        # The run_evaluation function is async, so we need to await it
        asyncio.run(
            run_evaluation(
                generated_workflow_dir=str(tmpdir),
            )
        )

    assert results_path.exists(), "evaluation_results.json was not created"
