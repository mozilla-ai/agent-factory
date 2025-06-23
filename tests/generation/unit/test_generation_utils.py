from unittest.mock import MagicMock, patch

import pytest
from any_agent import AgentRunError, AgentTrace

from agent_factory.generation import (
    run_agent,
    setup_output_directory,
)


class TestSetupOutputDirectory:
    def test_with_none_creates_unique_directory(self, tmp_path):
        """Ensures that passing None as output_dir creates a unique directory."""
        with patch("agent_factory.generation.Path.cwd", return_value=tmp_path):
            with patch("agent_factory.generation.datetime") as mock_datetime:
                mock_datetime.now.return_value.strftime.return_value = "2025-01-01_12:00:00"
                with patch("agent_factory.generation.uuid.uuid4") as mock_uuid:
                    mock_uuid.return_value.hex = "1234567890abcdef"  # pragma: allowlist secret

                    result = setup_output_directory()

                    # Check the directory structure pattern
                    assert "generated_workflows" in str(result)
                    assert "2025-01-01_12:00:00_" in str(result)
                    assert result.exists()

    def test_with_existing_dir_returns_same_dir(self, tmp_path):
        """Ensures that passing an existing directory as output_dir returns the same directory."""
        result = setup_output_directory(tmp_path)
        assert result == tmp_path
        assert result.exists()

    def test_creates_nonexistent_parents(self, tmp_path):
        """Verifies that the function creates parent directories if they don't exist."""
        target_dir = tmp_path / "nonexistent" / "subdir"
        result = setup_output_directory(target_dir)
        assert result == target_dir
        assert result.exists()


class TestRunAgent:
    def test_successful_run_returns_trace(self):
        """Tests that run_agent returns the AgentTrace object when the agent runs successfully."""
        mock_agent = MagicMock(spec=["run"])
        max_turns = 30
        expected_trace = AgentTrace()
        mock_agent.run.return_value = expected_trace

        result = run_agent(mock_agent, "test prompt")

        assert result == expected_trace
        mock_agent.run.assert_called_once_with("test prompt", max_turns=max_turns)

    def test_agent_run_error_returns_trace(self):
        """Tests that when an AgentRunError occurs, the trace is returned."""
        # Create a mock trace that will be passed to AgentRunError
        expected_trace = AgentTrace()

        # Create the error with the trace
        error = AgentRunError(trace=expected_trace)

        mock_agent = MagicMock(spec=["run"])
        mock_agent.run.side_effect = error

        with patch("builtins.print") as mock_print:
            result = run_agent(mock_agent, "test prompt")

            assert result == expected_trace
            mock_print.assert_any_call("Agent execution failed: " + str(error))
            mock_print.assert_any_call("Retrieved partial agent trace...")

    def test_unexpected_error_raises(self):
        """Tests that when an unexpected error occurs, it's wrapped in a RuntimeError and re-raised."""
        # Create a mock agent
        mock_agent = MagicMock(spec=["run"])
        error = RuntimeError("Critical failure")
        mock_agent.run.side_effect = error

        # The error should be wrapped in a RuntimeError with the original error as cause
        with pytest.raises(RuntimeError, match="Unexpected error during agent execution") as exc_info:
            run_agent(mock_agent, "test prompt")

        # Verify the original error is preserved as the cause
        assert "Critical failure" in str(exc_info.value)
