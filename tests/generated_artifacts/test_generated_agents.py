from pathlib import Path

import pytest

ARTIFACTS_PATH = Path(__file__).parent.parent / "artifacts"


@pytest.fixture(
    params=list(ARTIFACTS_PATH.rglob("*agent.py")),
    ids=lambda x: x.parent.name,
)
def generated_agent_code(request: pytest.FixtureRequest) -> str:
    return request.param.read_text()


def test_specific_tool_used(generated_agent_code: str, request: pytest.FixtureRequest):
    if "url-to-podcast" in request.node.callspec.id:
        # TODO: more elaborated asserts based on actually importing the code and checking the variables
        assert "extract_text_from_url" in generated_agent_code
        assert "generate_podcast_script_with_llm" in generated_agent_code
        assert "ELEVENLABS_API_KEY" in generated_agent_code
        # TODO: how to assert that only subset of MCP server's tools are used?
    elif "summarize-url-content" in request.node.callspec.id:
        assert "extract_text_from_url" in generated_agent_code
        assert "summarize_text_with_llm" in generated_agent_code
        # TODO: how to assert that no MCP server is used - it tends to be imported even though not used


def test_partial_trace_handling(generated_agent_code: str):
    """Test that the generated agent includes proper partial trace handling."""
    assert "except AgentRunError as e:" in generated_agent_code
    assert "agent_trace = e.trace" in generated_agent_code
    assert "partial" in generated_agent_code.lower() and "trace" in generated_agent_code.lower()
