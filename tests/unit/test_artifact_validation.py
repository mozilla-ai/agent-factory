"""Tests for artifact validation utilities."""

import pytest

from agent_factory.utils.artifact_validation import PINNED_ANY_LLM, validate_dependencies


class TestValidateDependencies:
    """Test the validate_dependencies function."""

    def test_basic_validation_adds_anyllm(self, sample_generator_agent_response_json):
        """Test that PINNED_ANY_LLM is added to typical agent dependencies."""
        agent_factory_outputs = sample_generator_agent_response_json.copy()

        result = validate_dependencies(agent_factory_outputs)

        expected = sample_generator_agent_response_json["dependencies"] + "\n" + PINNED_ANY_LLM
        assert result == expected
        assert agent_factory_outputs["dependencies"] == expected

    @pytest.mark.parametrize(
        "anyllm_dep,expected_suffix",
        [
            ("any-llm-sdk", PINNED_ANY_LLM),
            ("any-llm-sdk[openai]=>0.10.0", PINNED_ANY_LLM),
            ("any-llm-sdk[ollama]==0.13.1", PINNED_ANY_LLM),
        ],
    )
    def test_replaces_existing_anyllm_versions(self, sample_generator_agent_response_json, anyllm_dep, expected_suffix):
        """Test that existing any-llm versions are replaced with PINNED_ANY_LLM."""
        agent_factory_outputs = sample_generator_agent_response_json.copy()
        agent_factory_outputs["dependencies"] = sample_generator_agent_response_json["dependencies"] + f"\n{anyllm_dep}"

        result = validate_dependencies(agent_factory_outputs)

        expected = sample_generator_agent_response_json["dependencies"] + f"\n{expected_suffix}"
        assert result == expected
        assert result.count(PINNED_ANY_LLM) == 1

    def test_adds_uv_when_uvx_in_tools(self, sample_generator_agent_response_json):
        """Test that uv is added when uvx is found in tools."""
        agent_factory_outputs = sample_generator_agent_response_json.copy()
        # Modify tools to include uvx usage (realistic scenario)
        agent_factory_outputs["tools"] = (
            sample_generator_agent_response_json["tools"] + "\n# uvx install some-mcp-server"
        )

        result = validate_dependencies(agent_factory_outputs)

        expected = sample_generator_agent_response_json["dependencies"] + "\nuv\n" + PINNED_ANY_LLM
        assert result == expected
        assert agent_factory_outputs["dependencies"] == expected
