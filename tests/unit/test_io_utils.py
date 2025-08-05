from pathlib import Path

from agent_factory.instructions import AGENT_CODE_TEMPLATE
from agent_factory.utils.io_utils import prepare_agent_artifacts


def test_prepare_agent_artifacts(sample_generator_agent_response_json):
    """Test that prepare_agent_artifacts correctly prepares the artifacts."""
    artifacts = prepare_agent_artifacts(sample_generator_agent_response_json)

    assert "agent.py" in artifacts
    assert "README.md" in artifacts
    assert "requirements.txt" in artifacts
    assert "tools/__init__.py" in artifacts
    assert "tools/summarize_text_with_llm.py" in artifacts

    from agent_factory.utils import clean_python_code_with_autoflake

    agent_code_before_cleaning = AGENT_CODE_TEMPLATE.format(**sample_generator_agent_response_json)
    assert artifacts["agent.py"] == clean_python_code_with_autoflake(agent_code_before_cleaning)
    assert artifacts["README.md"] == sample_generator_agent_response_json["readme"]
    assert artifacts["requirements.txt"] == sample_generator_agent_response_json["dependencies"]

    # Verify tools taken from src directory
    tool_path = Path("src/agent_factory/tools/summarize_text_with_llm.py")
    assert artifacts["tools/summarize_text_with_llm.py"] == tool_path.read_text(encoding="utf-8")
