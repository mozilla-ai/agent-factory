import ast
import subprocess
import tempfile
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from shutil import copytree

import pytest
from any_agent.tracing.agent_trace import AgentTrace
from requirements_validators import (
    assert_mcp_uv_consistency,
    assert_requirements_first_line_matches_any_agent_version,
    assert_requirements_installable,
)

from agent_factory.generation import single_turn_generation
from agent_factory.utils.trace_utils import load_agent_trace


def _assert_generated_files(workflow_dir: Path):
    existing_files = [f.name for f in workflow_dir.iterdir()]
    for expected_file in ["agent.py", "INSTRUCTIONS.md", "requirements.txt", "agent_factory_trace.json"]:
        assert expected_file in existing_files, f"{expected_file} was not generated."


def _assert_agent_syntax(agent_file: Path):
    ast.parse(agent_file.read_text(encoding="utf-8"))


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


@pytest.mark.parametrize(
    ("prompt_id", "prompt", "expected_num_turns", "expected_execution_time"),
    [
        (
            "url-to-podcast",
            "Create a workflow that takes an input web URL and creates an audio podcast with multiple speakers.",
            30,
            180,
        ),
        # Add new "use cases" here, following this format:
        # prompt_id: the directory where the artifacts will be generated under the /tests/assets folder
        # prompt: the actual prompt to pass for agent generation
        # expected_num_turns: the threshold max number of turns for the agent to complete the task
        # expected_execution_time: the threshold max execution time (in seconds) for the agent to complete the task
    ],
)
def test_single_turn_generation(
    tmp_path: Path,
    prompt_id: str,
    prompt: str,
    expected_num_turns: int,
    expected_execution_time: int,
    request: pytest.FixtureRequest,
):
    single_turn_generation(user_prompt=prompt, output_dir=tmp_path)

    _assert_generated_files(tmp_path)

    # Verify the generated agent.py has valid Python syntax
    _assert_agent_syntax(tmp_path / "agent.py")

    # Assertions based on manufacturing agent's trace
    agent_trace = load_agent_trace(tmp_path / "agent_factory_trace.json")
    _assert_execution_time_within_limit(agent_trace, expected_execution_time)
    _assert_num_turns_within_limit(agent_trace, expected_num_turns)

    # Assertions based on requirements.txt
    assert_requirements_first_line_matches_any_agent_version(tmp_path / "requirements.txt")
    assert_mcp_uv_consistency(tmp_path / "agent.py", tmp_path / "requirements.txt")
    assert_requirements_installable(tmp_path / "requirements.txt")

    update_artifacts = request.config.getoption("--update-artifacts")

    if update_artifacts:
        copytree(tmp_path, Path(__file__).parent.parent / "artifacts" / prompt_id, dirs_exist_ok=True)
