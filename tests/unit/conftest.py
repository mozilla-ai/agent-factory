"""Configuration and fixtures for unit tests."""

import json
from pathlib import Path
from typing import Any

import pytest

UNIT_TESTS_DATA_DIR = Path(__file__).parent / "data"


@pytest.fixture
def mock_agent_card() -> dict[str, Any]:
    """Return the mock agent card data as a dictionary."""
    with (UNIT_TESTS_DATA_DIR / "mock_agent_card.json").open() as f:
        return json.load(f)
