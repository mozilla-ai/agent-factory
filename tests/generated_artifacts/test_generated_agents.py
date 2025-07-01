import subprocess
import sys
from pathlib import Path

import pytest

ARTIFACTS_PATH = Path(__file__).parent.parent / "artifacts"


@pytest.fixture(
    params=list(ARTIFACTS_PATH.rglob("*agent.py")),
    ids=lambda x: x.parent.name,
)
def generated_agent_code(request: pytest.FixtureRequest) -> str:
    return request.param.read_text()


@pytest.fixture(
    # assume the only valid dirs are those with an "agent.py" file in them
    params=[p.parent for p in ARTIFACTS_PATH.rglob("*agent.py")],
    ids=lambda x: x.name,
)
def generated_agent_path(request: pytest.FixtureRequest) -> str:
    return request.param


def test_specific_tool_used(generated_agent_code: str, request: pytest.FixtureRequest):
    if "url-to-podcast" in request.node.callspec.id:
        # TODO: more elaborated asserts based on actually importing the code and checking the variables
        assert "extract_text_from_url" in generated_agent_code
        assert "generate_podcast_script_with_llm" in generated_agent_code


def test_partial_trace_handling(generated_agent_code: str):
    """Test that the generated agent includes proper partial trace handling."""
    assert "except AgentRunError as e:" in generated_agent_code
    assert "agent_trace = e.trace" in generated_agent_code
    assert "partial" in generated_agent_code.lower() and "trace" in generated_agent_code.lower()


def test_agent_basic_execution(generated_agent_path: str, timeout: int = 15):
    """Test if the agent can start without immediate crash"""
    try:
        agent_file = Path(generated_agent_path) / "agent.py"
        agent_requirements = Path(generated_agent_path) / "requirements.txt"

        # Try to run the agent with a simple argument to see if it starts
        cmd = [
            "uv",
            "run",
            "--with-requirements",
            agent_requirements,
            "--python",
            "3.11",
            "python",
            agent_file,
            "--help",
        ]
        process = subprocess.run(
            cmd,
            timeout=timeout,  # Short timeout for basic execution test
            capture_output=True,
            text=True,
        )

        # make sure there are no import or syntax error in this basic execution
        assert "ImportError" not in process.stderr and "SyntaxError" not in process.stderr

    except subprocess.TimeoutExpired:
        # For basic execution, timeout likely means it is waiting for input or hanging
        pytest.fail(f"Timeout after {timeout} seconds - agent may be waiting for input or hanging")
    except Exception as e:
        pytest.fail(f"Basic execution test error: {e}")
