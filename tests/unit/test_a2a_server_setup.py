import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from any_agent.callbacks import get_default_callbacks

from agent_factory.callbacks import LimitAgentTurns


@pytest.mark.asyncio
@patch("any_agent.AnyAgent.create_async")
async def test_agent_created_with_specified_callbacks(mock_create_async):
    """Test that the agent is created with the default + specified callbacks."""
    mock_agent = AsyncMock()
    mock_create_async.return_value = mock_agent

    mock_server_handle = AsyncMock()
    mock_task = asyncio.Future()
    mock_task.set_result(None)
    mock_server_handle.task = mock_task
    mock_agent.serve_async.return_value = mock_server_handle

    from agent_factory.__main__ import main

    max_turns = 10
    await main(framework="openai", max_turns=max_turns)

    args, kwargs = mock_create_async.call_args
    assert args[0] == "openai"

    agent_config = args[1]

    expected_callbacks = get_default_callbacks() + [LimitAgentTurns(max_turns=max_turns)]
    expected_callback_types = {type(cb) for cb in expected_callbacks}
    callback_types_in_config = {type(cb) for cb in agent_config.callbacks}

    missing_defaults = expected_callback_types - callback_types_in_config
    assert not missing_defaults, f"Missing default callbacks: {missing_defaults}"

    limit_turns_cb = next(cb for cb in agent_config.callbacks if isinstance(cb, LimitAgentTurns))
    assert limit_turns_cb.max_turns == max_turns, f"max_turns should be {max_turns}"
