from unittest.mock import MagicMock, patch

import pytest
from any_agent import AgentRunError, AgentTrace

from agent.utils.io_utils import setup_output_directory
from agent_factory.generation import (
    run_agent,
)


def test_setup_output_directory_with_none_creates_unique_directory(tmp_path):
    """Ensures that passing None as output_dir creates a unique directory."""
    with patch("agent.utils.io_utils.Path.cwd", return_value=tmp_path):
        with patch("agent.utils.io_utils.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "2025-01-01_12:00:00"
            with patch("agent.utils.io_utils.uuid.uuid4") as mock_uuid:
                mock_uuid.return_value.hex = "1234567890abcdef"  # pragma: allowlist secret

                result = setup_output_directory()

                # Check the directory structure pattern
                assert "generated_workflows" in str(result)
                assert "2025-01-01_12:00:00_" in str(result)
                assert result.exists()


def test_setup_output_directory_with_existing_dir_returns_same_dir(tmp_path):
    """Ensures that passing an existing directory as output_dir returns the same directory."""
    result = setup_output_directory(tmp_path)
    assert result == tmp_path
    assert result.exists()


def test_setup_output_directory_creates_nonexistent_parents(tmp_path):
    """Verifies that the function creates parent directories if they don't exist."""
    target_dir = tmp_path / "nonexistent" / "subdir"
    result = setup_output_directory(target_dir)
    assert result == target_dir
    assert result.exists()


def test_run_agent_successful_returns_trace():
    """Tests that run_agent returns the AgentTrace object when the agent runs successfully."""
    mock_agent = MagicMock(spec=["run"])
    max_turns = 30
    expected_trace = AgentTrace()
    mock_agent.run.return_value = expected_trace

    result = run_agent(mock_agent, "test prompt")

    assert result == expected_trace
    mock_agent.run.assert_called_once_with("test prompt", max_turns=max_turns)


def test_run_agent_error_returns_trace():
    """Tests that when an AgentRunError occurs, the trace is returned."""
    # Create a mock trace that will be passed to AgentRunError
    expected_trace = AgentTrace()

    # Mock the cost property to avoid cost tracking errors
    mock_cost = MagicMock()
    mock_cost.input_cost = 0.0
    mock_cost.output_cost = 0.0
    mock_cost.total_cost = 0.0
    expected_trace.cost = mock_cost

    # Create the error with the trace
    error = AgentRunError(original_exception=Exception("Test error"), trace=expected_trace)

    mock_agent = MagicMock(spec=["run"])
    mock_agent.run.side_effect = error

    with patch("builtins.print") as mock_print:
        result = run_agent(mock_agent, "test prompt")

        assert result == expected_trace
        mock_print.assert_any_call("Agent execution failed: " + str(error))
        mock_print.assert_any_call("Retrieved partial agent trace...")
