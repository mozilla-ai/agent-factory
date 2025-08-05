import json
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import httpx
import pytest
from a2a.types import AgentCard

from agent_factory.schemas import AgentFactoryOutputs, Status
from agent_factory.utils.client_utils import (
    create_a2a_http_client,
    create_message_request,
    get_a2a_agent_card,
    process_a2a_agent_response,
)
from agent_factory.utils.io_utils import setup_output_directory


def test_setup_output_directory_with_none_creates_unique_directory(tmp_path):
    """Ensures that passing None as output_dir creates a unique directory."""
    with patch("agent_factory.utils.io_utils.Path.cwd", return_value=tmp_path):
        with patch("agent_factory.utils.io_utils.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "2025-01-01_12:00:00"
            with patch("agent_factory.utils.io_utils.uuid.uuid4") as mock_uuid:
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


@pytest.mark.asyncio
async def test_create_a2a_http_client_constructs_correct_url():
    """Test that the base URL is constructed correctly."""
    host = "test-host"
    port = 1234
    timeout = 600

    expected_url = f"http://{host}:{port}"

    client, base_url = await create_a2a_http_client(host, port, timeout)

    assert isinstance(client, httpx.AsyncClient)
    assert client.timeout.connect == timeout
    assert base_url == expected_url
    await client.aclose()


@pytest.mark.asyncio
async def test_get_a2a_agent_card_success(sample_a2a_agent_card):
    """Test successful retrieval of agent card."""
    expected_card = AgentCard(**sample_a2a_agent_card)

    mock_resolver = AsyncMock()
    mock_resolver.get_agent_card.return_value = expected_card

    result = await get_a2a_agent_card(mock_resolver)

    assert result == expected_card
    assert result.name == "test-agent"
    mock_resolver.get_agent_card.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_a2a_agent_card_error():
    """Test error handling when agent card retrieval fails."""
    mock_resolver = AsyncMock()
    test_error = Exception("Test error")
    mock_resolver.get_agent_card.side_effect = test_error

    with pytest.raises(RuntimeError) as exc_info:
        await get_a2a_agent_card(mock_resolver)

    assert "Failed to fetch the public agent card" in str(exc_info.value)
    assert exc_info.value.__cause__ is test_error


def test_create_message_request_basic():
    """Test basic message request creation."""
    test_message = "User prompt for the agent"
    request = create_message_request(test_message)

    assert hasattr(request, "id")
    assert hasattr(request, "params")
    assert hasattr(request.params, "message")

    message = request.params.message
    assert message.role == "user"
    assert len(message.parts) == 1
    assert message.parts[0].root.kind == "text"
    assert message.parts[0].root.text == test_message

    # Verify message ID has been set
    import re

    assert re.match(r"^[0-9a-f]{32}$", message.messageId) is not None


def test_create_message_request_empty_string_throws_error():
    """Test message request creation with empty or whitespace-only strings."""
    test_cases = ["", "   "]
    expected_error = "Message cannot be empty or whitespace only"

    for message in test_cases:
        with pytest.raises(ValueError) as exc_info:
            create_message_request(message)
        assert str(exc_info.value) == expected_error


@pytest.mark.parametrize(
    "request_id_input, is_valid_request_id",
    [
        (uuid4(), True),
        (str(uuid4()), True),
        ("not-a-uuid", False),
        (None, False),
    ],
)
def test_create_message_request_handles_request_id(request_id_input, is_valid_request_id):
    """Test that create_message_request handles request_id correctly."""
    test_message = "User prompt for the agent"

    expected_id = None
    if is_valid_request_id:
        expected_id = UUID(str(request_id_input))

    request = create_message_request(test_message, request_id=request_id_input)

    request_id = UUID(request.id)
    assert isinstance(request_id, UUID)
    if expected_id:
        assert request_id == expected_id


def test_process_a2a_agent_response_valid(mock_a2a_agent_response):
    """Test processing a valid agent response."""
    result = process_a2a_agent_response(mock_a2a_agent_response)

    assert isinstance(result, AgentFactoryOutputs)
    assert result.message == "✅ Done! Your agent is ready!"
    assert result.status == Status.COMPLETED
    assert "from any_agent.tools import search_tavily" in result.imports


def test_process_a2a_agent_response_missing_fields(mock_a2a_agent_response):
    """Test processing a response with missing required fields."""
    invalid_response = {"message": "Test"}  # Missing other required fields

    mock_a2a_agent_response.root.result.status.message.parts[0].root.text = json.dumps(invalid_response)

    with pytest.raises(ValueError) as exc_info:
        process_a2a_agent_response(mock_a2a_agent_response)

    assert "validation error" in str(exc_info.value).lower()
    assert "field required" in str(exc_info.value).lower()
