from pathlib import Path

import pytest

ASSETS_PATH = Path(__file__).parent / "assets"


@pytest.fixture(
    params=list(ASSETS_PATH.rglob("*agent.py")),
    ids=lambda x: x.parent.name,
)
def generated_agent_code(request: pytest.FixtureRequest) -> str:
    return request.param.read_text()


def test_specific_tool_used(generated_agent_code: str, request: pytest.FixtureRequest):
    if "url-to-podcast" in request.node.callspec.id:
        # TODO: more elaborated asserts based on actually importing the code and checking the variables
        assert "extract_text_from_url" in generated_agent_code
        assert "generate_podcast_script_with_llm" in generated_agent_code
