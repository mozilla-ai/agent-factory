from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from agent_factory.agent_generator import generate_target_agent
from agent_factory.schemas import Status


@pytest.mark.asyncio
async def test_generate_target_agent_success(mock_agent_generator_dependencies):
    """Tests the successful generation of an agent."""
    mocks = mock_agent_generator_dependencies
    mocks["process_a2a_agent_response"].return_value = MagicMock(status=Status.COMPLETED)

    await generate_target_agent("test message")

    mocks["create_a2a_http_client"].assert_called_once()
    mocks["get_a2a_agent_card"].assert_called_once()
    mocks["a2a_client"].assert_called_once()
    mocks["create_message_request"].assert_called_once_with("test message", request_id=None)
    mocks["a2a_client_instance"].send_message.assert_called_once()
    mocks["process_a2a_agent_response"].assert_called_once()
    mocks["prepare_agent_artifacts"].assert_called_once()
    mocks["get_storage_backend"].assert_called_once()
    mocks["storage_backend"].save.assert_called_once()


@pytest.mark.asyncio
async def test_generate_target_agent_input_required(mock_agent_generator_dependencies):
    """Tests the case where the agent requires more input."""
    mocks = mock_agent_generator_dependencies
    mocks["process_a2a_agent_response"].return_value = MagicMock(
        status=Status.INPUT_REQUIRED, message="Please provide more details."
    )

    await generate_target_agent("test message")

    mocks["logger"].info.assert_any_call("A2AClient initialized.")
    mocks["logger"].info.assert_any_call(
        "Please try again and be more specific with your request. Agent's response: Please provide more details."
    )


@pytest.mark.asyncio
async def test_generate_target_agent_error(mock_agent_generator_dependencies):
    """Tests the case where the agent returns an error."""
    mocks = mock_agent_generator_dependencies
    mocks["process_a2a_agent_response"].return_value = MagicMock(status=Status.ERROR, message="Agent error.")

    with pytest.raises(Exception, match="Agent encountered an error: Agent error."):
        await generate_target_agent("test message")

    mocks["logger"].info.assert_any_call("A2AClient initialized.")
    mocks["logger"].error.assert_called_with(
        "An unexpected error occurred during agent generation: Agent encountered an error: Agent error."
    )


@pytest.mark.asyncio
async def test_generate_target_agent_with_custom_output_dir(mock_agent_generator_dependencies):
    """Tests that a custom output directory is used when provided."""
    mocks = mock_agent_generator_dependencies
    mocks["process_a2a_agent_response"].return_value = MagicMock(status=Status.COMPLETED)

    await generate_target_agent("test message", output_dir="/custom/dir")

    mocks["prepare_agent_artifacts"].assert_called_once()
    mocks["get_storage_backend"].assert_called_once()
    mocks["storage_backend"].save.assert_called_once()
    # Verify that the output_dir was passed to the save function
    args, kwargs = mocks["storage_backend"].save.call_args
    assert args[1] == Path("/custom/dir")


@pytest.mark.asyncio
async def test_generate_target_agent_http_error():
    """Tests that HTTP errors are handled correctly."""
    with patch("agent_factory.agent_generator.create_a2a_http_client") as mock_create_a2a_http_client:
        mock_create_a2a_http_client.side_effect = Exception("Connection error")

        with pytest.raises(Exception, match="Connection error"):
            await generate_target_agent("test message")
