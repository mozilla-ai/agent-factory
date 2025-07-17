import json
from pathlib import Path

import pytest
from any_agent import AgentTrace


@pytest.fixture
def agent_factory_trace_file(artifacts_dir: Path, prompt_id: str) -> Path:
    """Fixture to get the trace file path for the current prompt."""
    return artifacts_dir / prompt_id / "agent_factory_trace.json"


@pytest.fixture
def agent_factory_trace(agent_factory_trace_file: Path) -> AgentTrace:
    """Fixture to load and validate the trace for the current prompt."""
    return AgentTrace.model_validate_json(agent_factory_trace_file.read_text())


def get_specific_tool_calls_by_name(trace: AgentTrace, tool_name: str) -> list:
    """Helper function to get all tool call args of a specific type from a trace."""
    specific_tool_call_args = []
    for span in trace.spans:
        if span.is_tool_execution():
            output_content = span.get_output_content()
            if output_content and span.attributes.get("gen_ai.tool.name") == tool_name:
                specific_tool_call_args.append(json.loads(json.loads(span.attributes["gen_ai.tool.args"])))
    return specific_tool_call_args


@pytest.mark.artifact_validation
def test_any_tool_used(agent_factory_trace: AgentTrace):
    """Test that at least one tool was used in the trace."""
    assert any(span.is_tool_execution() for span in agent_factory_trace.spans), "No tools were used"


@pytest.mark.artifact_validation
def test_search_mcp_servers_used(agent_factory_trace: AgentTrace, prompt_id: str):
    """Test if the search_mcp_servers tool was used as expected with the desired keyphrases."""
    if "summarize-url-content" in prompt_id:
        search_mcp_tool_calls = get_specific_tool_calls_by_name(agent_factory_trace, "search_mcp_servers")
        assert not search_mcp_tool_calls, "Use of MCP servers was not allowed for summarize-url-content workflow"
    elif "url-to-podcast" in prompt_id:
        search_mcp_tool_calls = get_specific_tool_calls_by_name(agent_factory_trace, "search_mcp_servers")
        assert search_mcp_tool_calls, "No search_mcp_servers tool calls found in the trace"
        keyphrases_used = [tool_args.get("keyphrase", "").lower() for tool_args in search_mcp_tool_calls]
        assert "elevenlabs" in keyphrases_used
    elif "scoring-blueprints-submission" in prompt_id:
        search_mcp_tool_calls = get_specific_tool_calls_by_name(agent_factory_trace, "search_mcp_servers")
        assert search_mcp_tool_calls, "No search_mcp_servers tool calls found in the trace"
        keyphrases_used = [tool_args.get("keyphrase", "").lower() for tool_args in search_mcp_tool_calls]
        assert "slack" in keyphrases_used
        assert "sqlite" in keyphrases_used
        # Only official servers are to be used, as per the user prompt
        assert all(tool_args.get("is_official") is True for tool_args in search_mcp_tool_calls)


@pytest.mark.artifact_validation
@pytest.mark.parametrize("max_steps", range(5, 30, 5))
def test_steps_taken(agent_factory_trace: AgentTrace, max_steps: int):
    """Test that the number of steps taken is within the expected range."""
    if max_steps <= len(agent_factory_trace.spans):
        pytest.xfail()
    assert len(agent_factory_trace.spans) < max_steps


@pytest.mark.artifact_validation
@pytest.mark.parametrize("max_tokens", range(1000, 50000, 5000))
def test_tokens_used(agent_factory_trace: AgentTrace, max_tokens: int):
    """Test that the number of tokens used is within the expected range."""
    if max_tokens <= agent_factory_trace.tokens.total_tokens:
        pytest.xfail()
    assert agent_factory_trace.tokens.total_tokens < max_tokens
