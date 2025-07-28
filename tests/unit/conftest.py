"""Configuration and fixtures for unit tests."""

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

UNIT_TESTS_DATA_DIR = Path(__file__).parent / "data"


@pytest.fixture
def mock_agent_card() -> dict[str, Any]:
    """Return the mock agent card data as a dictionary."""
    with (UNIT_TESTS_DATA_DIR / "mock_agent_card.json").open() as f:
        return json.load(f)


@pytest.fixture
def mock_agent_response():
    with (UNIT_TESTS_DATA_DIR / "mock_agent_response.json").open() as f:
        response_data = json.load(f)

    response_str = json.dumps(response_data)
    mock_response = MagicMock()
    mock_response.root.result.status.message.parts = [MagicMock(root=MagicMock(text=response_str))]

    return mock_response
