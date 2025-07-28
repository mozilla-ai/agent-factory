"""Configuration and fixtures for unit tests."""

import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

UNIT_TESTS_DATA_DIR = Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def mock_agent_card() -> dict[str, Any]:
    """Return the mock agent card data as a dictionary."""
    with (UNIT_TESTS_DATA_DIR / "mock_agent_card.json").open() as f:
        return json.load(f)


@pytest.fixture(scope="session")
def mock_agent_response():
    with (UNIT_TESTS_DATA_DIR / "mock_agent_response.json").open() as f:
        response_data = json.load(f)

    response_str = json.dumps(response_data)
    mock_response = MagicMock()
    mock_response.root.result.status.message.parts = [MagicMock(root=MagicMock(text=response_str))]

    return mock_response


@pytest.fixture(scope="function")
def mock_agent_generator_dependencies():
    """A fixture to mock all dependencies for generate_target_agent."""
    with (
        patch("agent_factory.agent_generator.create_a2a_http_client") as mock_create_a2a_http_client,
        patch("agent_factory.agent_generator.get_a2a_agent_card") as mock_get_a2a_agent_card,
        patch("agent_factory.agent_generator.A2AClient") as mock_a2a_client,
        patch("agent_factory.agent_generator.create_message_request") as mock_create_message_request,
        patch("agent_factory.agent_generator.process_a2a_agent_response") as mock_process_a2a_agent_response,
        patch("agent_factory.agent_generator.setup_output_directory") as mock_setup_output_directory,
        patch("agent_factory.agent_generator.save_agent_outputs") as mock_save_agent_outputs,
        patch("agent_factory.agent_generator.logger") as mock_logger,
    ):
        mock_http_client = AsyncMock()
        mock_create_a2a_http_client.return_value = (mock_http_client, "http://localhost:8080")
        mock_get_a2a_agent_card.return_value = MagicMock()
        mock_a2a_client_instance = MagicMock(spec=["send_message"])
        mock_a2a_client_instance.send_message = AsyncMock()
        mock_a2a_client.return_value = mock_a2a_client_instance

        mocks = {
            "create_a2a_http_client": mock_create_a2a_http_client,
            "get_a2a_agent_card": mock_get_a2a_agent_card,
            "a2a_client": mock_a2a_client,
            "a2a_client_instance": mock_a2a_client_instance,
            "create_message_request": mock_create_message_request,
            "process_a2a_agent_response": mock_process_a2a_agent_response,
            "setup_output_directory": mock_setup_output_directory,
            "save_agent_outputs": mock_save_agent_outputs,
            "logger": mock_logger,
        }

        yield mocks
