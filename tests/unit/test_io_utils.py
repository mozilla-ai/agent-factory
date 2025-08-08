import json
from pathlib import Path

import pytest

from agent_factory.instructions import AGENT_CODE_TEMPLATE
from agent_factory.schemas import AgentParameters
from agent_factory.utils.io_utils import (
    parse_cli_args_to_params_json,
    prepare_agent_artifacts,
)


def test_prepare_agent_artifacts(sample_generator_agent_response_json):
    """Test that prepare_agent_artifacts correctly prepares the artifacts."""
    artifacts = prepare_agent_artifacts(sample_generator_agent_response_json)

    assert "agent.py" in artifacts
    assert "README.md" in artifacts
    assert "requirements.txt" in artifacts
    assert "tools/__init__.py" in artifacts
    assert "tools/summarize_text_with_llm.py" in artifacts
    assert "agent_parameters.json" in artifacts

    from agent_factory.utils import clean_python_code_with_autoflake

    agent_code_before_cleaning = AGENT_CODE_TEMPLATE.format(**sample_generator_agent_response_json)
    assert artifacts["agent.py"] == clean_python_code_with_autoflake(agent_code_before_cleaning)
    assert artifacts["README.md"] == sample_generator_agent_response_json["readme"]
    assert artifacts["requirements.txt"] == sample_generator_agent_response_json["dependencies"]

    # Verify tools taken from src directory
    tool_path = Path("src/agent_factory/tools/summarize_text_with_llm.py")
    assert artifacts["tools/summarize_text_with_llm.py"] == tool_path.read_text(encoding="utf-8")

    assert artifacts["agent_parameters.json"] == parse_cli_args_to_params_json(
        sample_generator_agent_response_json["cli_args"]
    )


@pytest.mark.parametrize(
    "cli_args_str, expected_params",
    [
        # Single argument
        ("url: str", {"params": {"--url": "string"}}),
        # Multiple arguments
        ("url: str, num_hosts: int", {"params": {"--url": "string", "--num_hosts": "integer"}}),
        # Empty string
        ("", {"params": {}}),
    ],
)
def test_parse_cli_args_to_params_json(cli_args_str, expected_params):
    """Test that parse_cli_args_to_params_json correctly parses various CLI argument strings."""
    params_json_str = parse_cli_args_to_params_json(cli_args_str)
    actual_params = json.loads(params_json_str)
    assert actual_params == expected_params

    # Validate against the Pydantic schema
    validated_params = AgentParameters(**actual_params)
    assert validated_params.model_dump() == expected_params
