import ast
from pathlib import Path
from shutil import copytree

import pytest
from any_agent.tracing.agent_trace import AgentTrace
from requirements_validators import (
    assert_mcp_uv_consistency,
    assert_requirements_first_line_matches_any_agent_version,
    assert_requirements_installable,
)
from utils.non_deterministic_runs import run_until_success_threshold_async

from agent.utils.trace_utils import load_agent_trace
from agent_factory.generation import single_turn_generation


def _assert_generated_files(workflow_dir: Path):
    existing_files = [f.name for f in workflow_dir.iterdir()]
    expected_files = ["agent.py", "README.md", "requirements.txt", "agent_factory_trace.json"]

    for expected_file in expected_files:
        assert expected_file in existing_files, f"{expected_file} was not generated."

    extra_python_files = [f for f in existing_files if f.endswith(".py") and f != "agent.py"]
    assert len(extra_python_files) == 0, (
        f"Unexpected Python files found: {extra_python_files}. Only 'agent.py' should be generated."
    )


def _assert_agent_code_syntax(agent_file: Path):
    ast.parse(agent_file.read_text(encoding="utf-8"))


def _assert_agent_code_contains_trace_writing(agent_file: Path):
    """Assert that the agent file contains the code to write agent trace to a JSON file."""
    agent_code = agent_file.read_text(encoding="utf-8")

    assert all(
        pattern in agent_code
        for pattern in [
            "script_dir = Path(__file__).resolve().parent",
            'output_path = script_dir / "agent_eval_trace.json"',
            "trace_data = agent_trace.model_dump()",
            'trace_data["execution_costs"]',
            "f.write(json.dumps(trace_data, indent=2))",
        ]
    ), "agent.py has incorrect usage of writing the agent trace to a JSON file"


def _assert_execution_time_within_limit(agent_trace: AgentTrace, expected_execution_time: int) -> None:
    """Assert that the agent execution time is within the expected threshold.

    Args:
        agent_trace: The agent trace object
        expected_execution_time: Maximum allowed execution time in seconds
    """
    agent_execution_time_in_seconds = agent_trace.duration.total_seconds()
    assert agent_execution_time_in_seconds < expected_execution_time, (
        f"Agent execution time {agent_execution_time_in_seconds:.2f}s exceeded expected "
        f"threshold of {expected_execution_time}s"
    )


def _assert_num_turns_within_limit(agent_trace: AgentTrace, expected_num_turns: int) -> None:
    """Assert that the agent execution time is within the expected threshold.

    Args:
        agent_trace: The agent trace object
        expected_num_turns: Maximum allowed number of turns
    """
    num_turns = len(agent_trace.spans)
    assert num_turns < expected_num_turns, (
        f"Agent executed {num_turns} turns exceeded expected threshold of {expected_num_turns}"
    )


def validate_generated_artifacts(artifacts_dir: Path, prompt_id: str):
    """Run all agent validation tests using pytest's test runner.

    This function runs all tests marked with @pytest.mark.artifact_validation
    in the tests/generated_artifacts/ directory for the specified prompt_id.

    Args:
        artifacts_dir: Base directory containing the generated artifacts
        prompt_id: ID of the prompt being tested

    Raises:
        AssertionError: If any of the validation tests fail
    """
    import sys

    # Run pytest programmatically
    args = [
        "tests/generated_artifacts/",
        "-m",
        "artifact_validation",
        f"--artifacts-dir={str(artifacts_dir.absolute())}",
        f"--prompt-id={prompt_id}",
        "-v",  # verbose
        "--tb=short",  # shorter tracebacks
        "-s",  # show output
        "-x",
        "--no-header",
        "--no-summary",
    ]

    exit_code = pytest.main(args)

    if exit_code != 0:
        failure_details = ""
        if hasattr(sys, "last_value") and sys.last_value is not None:
            failure_details = f"\nFailure details: {str(sys.last_value)}"

        raise AssertionError(
            f"Agent validation tests failed for prompt '{prompt_id}' with exit code {exit_code}.{failure_details}"
        )


@pytest.mark.asyncio
@run_until_success_threshold_async(max_attempts=5, min_successes=4)
async def test_single_turn_generation(
    tmp_path: Path,
    request: pytest.FixtureRequest,
    cost_tracker: list[float],
    use_cases: dict,
):
    """Test the generation of a single turn agent and validate the generated artifacts.

    This test generates an agent based on the provided prompt and then runs validation
    tests on the generated artifacts.
    """
    # Get the prompt_id from command line or use default
    prompt_id = request.config.getoption("--prompt-id")

    if prompt_id not in use_cases:
        pytest.fail(f"Prompt ID '{prompt_id}' not found in test cases. Available IDs: {list(use_cases.keys())}")

    test_case = use_cases[prompt_id]

    # Generate the agent
    full_path = tmp_path / prompt_id
    await single_turn_generation(user_prompt=test_case["prompt"], output_dir=full_path, disable_printspan_callback=True)

    # Verify the expected files were generated
    _assert_generated_files(full_path)

    # Verify the generated agent.py has valid Python syntax
    agent_file = full_path / "agent.py"
    _assert_agent_code_syntax(agent_file)
    _assert_agent_code_contains_trace_writing(agent_file)

    # Assertions based on manufacturing agent's trace
    agent_trace = load_agent_trace(full_path / "agent_factory_trace.json")
    _assert_execution_time_within_limit(agent_trace, test_case["expected_execution_time"])
    _assert_num_turns_within_limit(agent_trace, test_case["expected_num_turns"])

    # Cost tracking for completed agent artifact generations (based on agent_factory_trace.json)
    cost_tracker.append(agent_trace.execution_costs.total_cost)

    # Assertions based on requirements.txt
    assert_requirements_first_line_matches_any_agent_version(full_path / "requirements.txt")
    assert_mcp_uv_consistency(full_path / "agent.py", full_path / "requirements.txt")
    assert_requirements_installable(full_path / "requirements.txt")

    # Run code and trace validation tests defined in tests/generated_artifacts/
    validate_generated_artifacts(tmp_path, prompt_id)

    update_artifacts = request.config.getoption("--update-artifacts")
    if update_artifacts:
        copytree(full_path, Path(__file__).parent.parent / "artifacts" / prompt_id, dirs_exist_ok=True)
