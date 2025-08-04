# This file makes docs/scripts a Python package
# This enables relative imports to work correctly with uv run

from enum import Enum


class TestStatus(Enum):
    """Enum for MCP server test status values."""

    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
