import json
from pathlib import Path

import pytest
from any_agent import AgentTrace

ARTIFACTS_PATH = Path(__file__).parent.parent / "artifacts"


@pytest.fixture(
    params=list(ARTIFACTS_PATH.rglob("*_trace.json")),
    ids=lambda x: x.parent.name,
)
def generated_trace(request: pytest.FixtureRequest) -> AgentTrace:
    return AgentTrace.model_validate_json(request.param.read_text())


def test_any_tool_used(generated_trace: AgentTrace):
    assert any(span.is_tool_execution() for span in generated_trace.spans), "No tools were used"


def get_specific_tool_calls_by_name(trace: AgentTrace, tool_name: str) -> list:
    """Helper function to get all tool call args of a specific type from a trace."""
    specific_tool_call_args = []
    for span in trace.spans:
        if span.is_tool_execution():
            output_content = span.get_output_content()
            if output_content and span.attributes.get("gen_ai.tool.name") == tool_name:
                specific_tool_call_args.append(json.loads(span.attributes["gen_ai.tool.args"]))
    return specific_tool_call_args


def test_search_mcp_servers_used(generated_trace: AgentTrace, request: pytest.FixtureRequest):
    """On a per-usecase basis, test if the search_mcp_servers tool was used as expected with the desired keyphrases."""
    if "summarize-url-content" in request.node.callspec.id:
        search_mcp_tool_calls = get_specific_tool_calls_by_name(generated_trace, "search_mcp_servers")
        assert not search_mcp_tool_calls, "Use of MCP servers was not allowed for summarize-url-content workflow"
    elif "url-to-podcast" in request.node.callspec.id:
        search_mcp_tool_calls = get_specific_tool_calls_by_name(generated_trace, "search_mcp_servers")
        assert search_mcp_tool_calls, "No search_mcp_servers tool calls found in the trace"
        keyphrases_used = [tool_args.get("keyphrase").lower() for tool_args in search_mcp_tool_calls]
        assert "elevenlabs" in keyphrases_used
    elif "scoring-blueprints-submission" in request.node.callspec.id:
        search_mcp_tool_calls = get_specific_tool_calls_by_name(generated_trace, "search_mcp_servers")
        assert search_mcp_tool_calls, "No search_mcp_servers tool calls found in the trace"
        keyphrases_used = [tool_args.get("keyphrase").lower() for tool_args in search_mcp_tool_calls]
        assert "slack" in keyphrases_used
        assert "sqlite" in keyphrases_used


@pytest.mark.parametrize("max_steps", range(5, 30, 5))
def test_steps_taken(generated_trace: AgentTrace, max_steps: int):
    if max_steps <= len(generated_trace.spans):
        pytest.xfail()
    assert len(generated_trace.spans) < max_steps


@pytest.mark.parametrize("max_tokens", range(1000, 50000, 5000))
def test_tokens_used(generated_trace: AgentTrace, max_tokens: int):
    if max_tokens <= generated_trace.tokens.total_tokens:
        pytest.xfail()
    assert generated_trace.tokens.total_tokens < max_tokens
