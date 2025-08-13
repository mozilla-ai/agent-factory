"""Configuration and fixtures for unit tests."""

import json
import os
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

UNIT_TESTS_DATA_DIR = Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def sample_a2a_agent_card() -> dict[str, Any]:
    """Return the mock agent card data as a dictionary."""
    with (UNIT_TESTS_DATA_DIR / "sample_a2a_agent_card.json").open() as f:
        return json.load(f)


@pytest.fixture(scope="session")
def sample_generator_agent_response_json() -> dict[str, Any]:
    with (UNIT_TESTS_DATA_DIR / "sample_generator_agent_response.json").open() as f:
        return json.load(f)


@pytest.fixture(scope="session")
def mock_a2a_agent_response(sample_generator_agent_response_json) -> MagicMock:
    response_str = json.dumps(sample_generator_agent_response_json)
    mock_response = MagicMock()
    mock_response.root.result.status.message.parts = [MagicMock(root=MagicMock(text=response_str))]
    return mock_response


@pytest.fixture(scope="function")
def mock_a2a_agent_streaming_response():
    """Mock A2A agent streaming response with customizable state and message data.

    Args:
        state: The task state (e.g., TaskState.submitted, TaskState.working)
        message_data: Optional message data to include in the response

    Returns:
        A mock response object with the specified state and message data
    """

    def _create_mock_response(state, message_data=None):
        response = MagicMock()
        response.root.result.status.state = state

        if message_data is not None:
            part = MagicMock()
            part.root.data = message_data
            response.root.result.status.message.parts = [part]

        return response

    return _create_mock_response


@pytest.fixture(scope="function")
def mock_agent_generator_dependencies():
    """A fixture to mock all dependencies for generate_target_agent."""
    with (
        patch("agent_factory.agent_generator.create_a2a_http_client") as mock_create_a2a_http_client,
        patch("agent_factory.agent_generator.get_a2a_agent_card") as mock_get_a2a_agent_card,
        patch("agent_factory.agent_generator.A2AClient") as mock_a2a_client,
        patch("agent_factory.agent_generator.create_message_request") as mock_create_message_request,
        patch(
            "agent_factory.agent_generator.process_streaming_response_message"
        ) as mock_process_streaming_response_message,
        patch(
            "agent_factory.agent_generator.process_a2a_agent_final_response"
        ) as mock_process_a2a_agent_final_response,
        patch("agent_factory.agent_generator.prepare_agent_artifacts") as mock_prepare_agent_artifacts,
        patch("agent_factory.agent_generator.get_storage_backend") as mock_get_storage_backend,
        patch("agent_factory.agent_generator.logger") as mock_logger,
    ):
        mock_http_client = AsyncMock()
        mock_create_a2a_http_client.return_value = (mock_http_client, "http://localhost:8080")
        mock_get_a2a_agent_card.return_value = MagicMock()
        mock_a2a_client_instance = MagicMock(spec=["send_message", "send_message_streaming"])

        async def async_generator():
            yield MagicMock()

        mock_a2a_client_instance.send_message_streaming.return_value = async_generator()
        mock_a2a_client.return_value = mock_a2a_client_instance
        mock_storage_backend = MagicMock()
        mock_get_storage_backend.return_value = mock_storage_backend

        mocks = {
            "create_a2a_http_client": mock_create_a2a_http_client,
            "get_a2a_agent_card": mock_get_a2a_agent_card,
            "a2a_client": mock_a2a_client,
            "a2a_client_instance": mock_a2a_client_instance,
            "create_message_request": mock_create_message_request,
            "process_streaming_response_message": mock_process_streaming_response_message,
            "process_a2a_agent_final_response": mock_process_a2a_agent_final_response,
            "prepare_agent_artifacts": mock_prepare_agent_artifacts,
            "get_storage_backend": mock_get_storage_backend,
            "storage_backend": mock_storage_backend,
            "logger": mock_logger,
        }

        yield mocks


@pytest.fixture
def mock_s3_environ():
    """Mock S3 environment variables."""
    with patch.dict(
        os.environ,
        {
            "AWS_ACCESS_KEY_ID": "test-key",  # pragma: allowlist secret
            "AWS_SECRET_ACCESS_KEY": "test-secret",  # pragma: allowlist secret
            "AWS_REGION": "us-east-1",
            "S3_BUCKET_NAME": "test-bucket",
        },
    ) as patched_environ:
        yield patched_environ
