"""Tests for artifact validation utilities."""

import pytest

from agent_factory.utils.artifact_validation import validate_dependencies


class TestValidateDependencies:
    """Test the validate_dependencies function."""

    def test_basic_validation_adds_litellm(self, sample_generator_agent_response_json):
        """Test that litellm<1.75.0 is added to typical agent dependencies."""
        tools = sample_generator_agent_response_json["tools"]
        dependencies = []

        result = validate_dependencies(tools, dependencies)

        expected = "litellm<1.75.0"
        assert result.strip() == expected

    @pytest.mark.parametrize(
        "litellm_dep,expected_suffix",
        [
            ("litellm", "litellm<1.75.0"),
            ("litellm=>1.73.0", "litellm<1.75.0"),
            ("litellm[proxy]==1.80.0", "litellm<1.75.0"),
        ],
    )
    def test_replaces_existing_litellm_versions(
        self, sample_generator_agent_response_json, litellm_dep, expected_suffix
    ):
        """Test that existing litellm versions are replaced with pinned version."""
        tools = sample_generator_agent_response_json["tools"]
        dependencies = [litellm_dep]

        result = validate_dependencies(tools, dependencies)

        expected = expected_suffix
        assert result.strip() == expected
        assert result.count("litellm<1.75.0") == 1

    def test_adds_uv_when_uvx_in_tools(self, sample_generator_agent_response_json):
        """Test that uv is added when uvx is found in tools."""
        tools = sample_generator_agent_response_json["tools"] + "\n# uvx install some-mcp-server"
        dependencies = ["any-agent[all,a2a]==0.25.0", "python-dotenv", "beautifulsoup4", "requests", "fire"]

        result = validate_dependencies(tools, dependencies)

        expected = "\n".join(dependencies) + "\nuv\nlitellm<1.75.0"

        expected_sorted = sorted([line for line in expected.split("\n") if line])
        result_sorted = sorted([line for line in result.split("\n") if line])

        assert result_sorted == expected_sorted
