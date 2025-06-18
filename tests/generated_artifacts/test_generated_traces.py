from pathlib import Path

import pytest
from any_agent import AgentTrace

ASSETS_PATH = Path(__file__).parent.parent / "assets"


@pytest.fixture(
    params=list(ASSETS_PATH.rglob("*_trace.json")),
    ids=lambda x: x.parent.name,
)
def generated_trace(request: pytest.FixtureRequest) -> AgentTrace:
    return AgentTrace.model_validate_json(request.param.read_text())


def test_any_tool_used(generated_trace: AgentTrace):
    assert any(span.is_tool_execution() for span in generated_trace.spans), "No tools were used"


@pytest.mark.parametrize("max_steps", range(5, 30, 5))
def test_steps_taken(generated_trace: AgentTrace, max_steps: int, request: pytest.FixtureRequest):
    if "url-to-podcast" in request.node.callspec.id:
        if max_steps <= len(generated_trace.spans):
            pytest.xfail()
    assert len(generated_trace.spans) < max_steps


@pytest.mark.parametrize("max_tokens", range(1000, 50000, 5000))
def test_tokens_used(generated_trace: AgentTrace, max_tokens: int, request: pytest.FixtureRequest):
    if "url-to-podcast" in request.node.callspec.id:
        if max_tokens <= generated_trace.tokens.total_tokens:
            pytest.xfail()
    assert generated_trace.tokens.total_tokens < max_tokens
