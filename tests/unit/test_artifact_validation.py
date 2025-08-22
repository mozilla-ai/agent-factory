"""Tests for artifact validation utilities."""

import pytest

from agent_factory.utils.artifact_validation import validate_dependencies


class TestValidateDependencies:
    """Test the validate_dependencies function."""

    def test_basic_validation_adds_litellm(self, sample_generator_agent_response_json):
        """Test that litellm<1.75.0 is added to typical agent dependencies."""
        agent_factory_outputs = sample_generator_agent_response_json.copy()

        result = validate_dependencies(agent_factory_outputs)

        expected = sample_generator_agent_response_json["dependencies"] + "\nlitellm<1.75.0"
        assert result == expected
        assert agent_factory_outputs["dependencies"] == expected

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
        agent_factory_outputs = sample_generator_agent_response_json.copy()
        agent_factory_outputs["dependencies"] = (
            sample_generator_agent_response_json["dependencies"] + f"\n{litellm_dep}"
        )

        result = validate_dependencies(agent_factory_outputs)

        expected = sample_generator_agent_response_json["dependencies"] + f"\n{expected_suffix}"
        assert result == expected
        assert result.count("litellm<1.75.0") == 1

    def test_adds_uv_when_uvx_in_tools(self, sample_generator_agent_response_json):
        """Test that uv is added when uvx is found in tools."""
        agent_factory_outputs = sample_generator_agent_response_json.copy()
        # Modify tools to include uvx usage (realistic scenario)
        agent_factory_outputs["tools"] = (
            sample_generator_agent_response_json["tools"] + "\n# uvx install some-mcp-server"
        )

        result = validate_dependencies(agent_factory_outputs)

        expected = sample_generator_agent_response_json["dependencies"] + "\nuv\nlitellm<1.75.0"
        assert result == expected
        assert agent_factory_outputs["dependencies"] == expected
