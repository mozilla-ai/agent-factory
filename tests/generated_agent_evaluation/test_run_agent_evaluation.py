import asyncio
from unittest import mock

import pytest
from any_agent import AgentFramework
from eval.run_generated_agent_evaluation import run_evaluation


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


@pytest.mark.parametrize(
    "custom_model,custom_framework",
    [
        ("openai:o3", AgentFramework.OPENAI),
        ("openai:gpt-5", AgentFramework.GOOGLE),
        ("mistral:mistral-medium-2508", AgentFramework.LANGCHAIN),
        ("llama-2-70b", AgentFramework.SMOLAGENTS),
    ],
)
def test_evaluation_uses_custom_model_and_framework(
    tmpdir,
    sample_evaluation_json_file: str,
    sample_agent_eval_trace_json: str,
    custom_model: str,
    custom_framework: AgentFramework,
):
    """Tests that the AgentJudge uses the correct custom model and framework when provided."""
    evaluation_case_path = tmpdir.join("evaluation_case.json")
    evaluation_case_path.write(sample_evaluation_json_file)

    agent_trace_path = tmpdir.join("agent_eval_trace.json")
    agent_trace_path.write(sample_agent_eval_trace_json)

    with mock.patch("builtins.print"), mock.patch("eval.run_generated_agent_evaluation.AgentJudge") as mock_judge_class:
        mock_judge_instance = mock.Mock()
        mock_judge_instance.run_async.return_value = mock.Mock()
        mock_judge_class.return_value = mock_judge_instance

        asyncio.run(
            run_evaluation(
                generated_workflow_dir=str(tmpdir),
                framework=custom_framework,
                model=custom_model,
            )
        )

        mock_judge_class.assert_called_once_with(model_id=custom_model, framework=custom_framework)


def test_evaluation_uses_default_model_and_framework(
    tmpdir, sample_evaluation_json_file: str, sample_agent_eval_trace_json: str
):
    """Tests that the AgentJudge uses the default model and framework when we do not provide anything."""
    expected_default_model = "gpt-4.1"
    expected_default_framework = AgentFramework.TINYAGENT

    evaluation_case_path = tmpdir.join("evaluation_case.json")
    evaluation_case_path.write(sample_evaluation_json_file)

    agent_trace_path = tmpdir.join("agent_eval_trace.json")
    agent_trace_path.write(sample_agent_eval_trace_json)

    with mock.patch("builtins.print"), mock.patch("eval.run_generated_agent_evaluation.AgentJudge") as mock_judge_class:
        mock_judge_instance = mock.Mock()
        mock_judge_instance.run_async.return_value = mock.Mock()
        mock_judge_class.return_value = mock_judge_instance

        asyncio.run(
            run_evaluation(
                generated_workflow_dir=str(tmpdir),
            )
        )

        mock_judge_class.assert_called_once_with(model_id=expected_default_model, framework=expected_default_framework)
