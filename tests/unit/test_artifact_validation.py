"""Tests for artifact validation utilities."""

import pytest

from agent_factory.utils.artifact_validation import validate_dependencies


class TestValidateDependencies:
    """Test the validate_dependencies function."""

    def test_adds_uv_when_uvx_in_tools(self, sample_generator_agent_response_json):
        """Test that uv is added when uvx is found in tools."""
        tools = sample_generator_agent_response_json["tools"] + "\n# uvx install some-mcp-server"
        dependencies = ["any-agent[all,a2a]==0.25.0", "python-dotenv", "beautifulsoup4", "requests", "fire"]

        result = validate_dependencies(tools, dependencies)

        expected = "\n".join(dependencies) + "\nuv"

        expected_sorted = sorted([line for line in expected.split("\n") if line])
        result_sorted = sorted([line for line in result.split("\n") if line])

        assert result_sorted == expected_sorted
