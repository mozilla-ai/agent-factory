from unittest.mock import MagicMock

import pytest

from agent_factory.callbacks import LimitAgentTurns


def test_limit_agent_turns_exceeds_limit():
    """Test that the callback raises an exception when exceeding max_turns."""
    mock_context = MagicMock()
    mock_context.shared = {}
    max_turns = 1
    callback = LimitAgentTurns(max_turns)

    # First turn - no errors
    result = callback.before_llm_call(mock_context)
    assert result.shared["n_agent_turns"] == 1

    with pytest.raises(RuntimeError) as exc_info:
        callback.before_llm_call(mock_context)
    assert str(exc_info.value) == f"Reached limit of agent turns: {max_turns}"
