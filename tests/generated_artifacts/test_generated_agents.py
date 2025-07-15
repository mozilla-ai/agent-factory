import subprocess
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
    if "summarize-url-content" in request.node.callspec.id:
        assert "extract_text_from_url" in generated_agent_code
        assert "summarize_text_with_llm" in generated_agent_code
        assert all(term not in generated_agent_code for term in ("MCPStdio", "MCPSse")), (
            "MCP server not required for summarize-url-content workflow"
        )
    elif "url-to-podcast" in request.node.callspec.id:
        # Either visit_webpage or extract_text_from_url should be used, using both is also fine
        assert any(term in generated_agent_code for term in ("visit_webpage", "extract_text_from_url"))
        assert "generate_podcast_script_with_llm" in generated_agent_code
        assert "combine_mp3_files_for_podcast" in generated_agent_code
        # ElevenLabs MCP related code matching
        assert "ELEVENLABS_API_KEY" in generated_agent_code
        assert any(term in generated_agent_code for term in ("MCPStdio", "MCPSse")), (
            "MCP server(s) required for url-to-podcast workflow"
        )
        # Necessary ElevenLabs MCP tools used
        assert "generate_audio_" in generated_agent_code
        # Non-essential tools NOT used
        assert all(term not in generated_agent_code for term in ("delete_job", "get_voiceover_history"))

    elif "scoring-blueprints-submission":
        # Either visit_webpage or extract_text_from_url should be used, using both is also fine
        assert any(term in generated_agent_code for term in ("visit_webpage", "extract_text_from_url"))
        # Slack MCP related code matching
        assert any(term in generated_agent_code for term in ("MCPStdio", "MCPSse")), (
            "MCP server(s) required for scoring-blueprints-submission workflow"
        )
        assert all(term in generated_agent_code for term in ("SLACK_BOT_TOKEN", "SLACK_TEAM_ID"))
        assert "slack_list_channels" in generated_agent_code
        assert "slack_post_message" in generated_agent_code
        # SQLlite related code matching
        assert "mcp/sqlite" in generated_agent_code
        assert "write_query" in generated_agent_code
        assert "github_repo_evaluations" in generated_agent_code
        assert "blueprints.db" in generated_agent_code
        # Non-essential tools NOT used
        assert all(
            term not in generated_agent_code
            for term in ("slack_get_users", "slack_get_channel_history", "slack_get_user_profile")
        )
        assert all(term not in generated_agent_code for term in ("create_table", "append_insight"))

    elif "slack-newsletter":
        # Require search_tavily, extract_text_from_url, summarize_text_with_llm to be present
        assert "search_tavily" in generated_agent_code
        assert "extract_text_from_url" in generated_agent_code
        assert "summarize_text_with_llm" in generated_agent_code
        # Slack MCP related code matching
        assert any(term in generated_agent_code for term in ("MCPStdio", "MCPSse")), (
            "MCP server(s) required for scoring-blueprints-submission workflow"
        )
        # Ensure Slack is the only MCP server referenced
        assert generated_agent_code.count("mcp/slack") == generated_agent_code.count("mcp/"), (
            "Only mcp/slack should be referenced"
        )
        assert all(term in generated_agent_code for term in ("SLACK_BOT_TOKEN", "SLACK_TEAM_ID"))
        assert "slack_list_channels" in generated_agent_code
        assert "slack_post_message" in generated_agent_code
        # Non-essential tools NOT used
        assert all(
            term not in generated_agent_code
            for term in ("slack_get_users", "slack_get_channel_history", "slack_get_user_profile")
        )


def test_partial_trace_handling(generated_agent_code: str):
    """Test that the generated agent includes proper partial trace handling."""
    assert "except AgentRunError as e:" in generated_agent_code
    assert "agent_trace = e.trace" in generated_agent_code
    assert "partial" in generated_agent_code.lower() and "trace" in generated_agent_code.lower()


def test_agent_basic_execution(generated_agent_path: str, timeout: int = 30):
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
            "3.13",
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
