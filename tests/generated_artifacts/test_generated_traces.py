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
