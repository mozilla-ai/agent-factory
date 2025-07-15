import ast
import json
from pathlib import Path
from shutil import copytree

import pytest
from any_agent.tracing.agent_trace import AgentTrace
from requirements_validators import (
    assert_mcp_uv_consistency,
    assert_requirements_first_line_matches_any_agent_version,
    assert_requirements_installable,
)

from agent.utils.trace_utils import load_agent_trace
from agent_factory.generation import single_turn_generation


def _assert_generated_files(workflow_dir: Path):
    existing_files = [f.name for f in workflow_dir.iterdir()]
    expected_files = ["agent.py", "README.md", "requirements.txt", "agent_factory_trace.json"]

    for expected_file in expected_files:
        assert expected_file in existing_files, f"{expected_file} was not generated."

    extra_python_files = [f for f in existing_files if f.endswith(".py") and f != "agent.py"]
    assert len(extra_python_files) == 0, (
        f"Unexpected Python files found: {extra_python_files}. Only 'agent.py' should be generated."
    )


def _assert_agent_code_syntax(agent_file: Path):
    ast.parse(agent_file.read_text(encoding="utf-8"))


def _assert_agent_code_contains_trace_writing(agent_file: Path):
    """Assert that the agent file contains the code to write agent trace to a JSON file."""
    agent_code = agent_file.read_text(encoding="utf-8")

    assert all(
        pattern in agent_code
        for pattern in [
            "script_dir = Path(__file__).resolve().parent",
            'output_path = script_dir / "agent_eval_trace.json"',
            "trace_data = agent_trace.model_dump()",
            'trace_data["execution_costs"]',
            "f.write(json.dumps(trace_data, indent=2))",
        ]
    ), "agent.py has incorrect usage of writing the agent trace to a JSON file"


def _assert_execution_time_within_limit(agent_trace: AgentTrace, expected_execution_time: int) -> None:
    """Assert that the agent execution time is within the expected threshold.

    Args:
        agent_trace: The agent trace object
        expected_execution_time: Maximum allowed execution time in seconds
    """
    agent_execution_time_in_seconds = agent_trace.duration.total_seconds()
    assert agent_execution_time_in_seconds < expected_execution_time, (
        f"Agent execution time {agent_execution_time_in_seconds:.2f}s exceeded expected "
        f"threshold of {expected_execution_time}s"
    )


def _assert_num_turns_within_limit(agent_trace: AgentTrace, expected_num_turns: int) -> None:
    """Assert that the agent execution time is within the expected threshold.

    Args:
        agent_trace: The agent trace object
        expected_num_turns: Maximum allowed number of turns
    """
    num_turns = len(agent_trace.spans)
    assert num_turns < expected_num_turns, (
        f"Agent executed {num_turns} turns exceeded expected threshold of {expected_num_turns}"
    )


@pytest.mark.parametrize(
    ("prompt_id", "prompt", "expected_num_turns", "expected_execution_time"),
    [
        # Agent with no MCP tools needed
        (
            "summarize-url-content",
            (
                "Workflow that takes an input web URL and returns a summary of the content. "
                "Do not search for or assign MCP servers among the tools."
            ),
            15,
            120,
        ),
        # Agent with MCP single MCP server (ElevenLabs)
        (
            "url-to-podcast",
            (
                "Workflow to generate a 1-minute podcast mp3 based on the contents of a URL provided by the user. "
                "And it should create separate mp3 files interleaving the turn-by-turn dialogue between a host and a guest speaker. "
                "The final output should be saved as a single mp3 file. "
                "Use audio generation tools from ElevenLabs API for text-to-speech."
            ),
            30,
            300,
        ),
        # Agent with multiple MCP servers (Slack and SQLite)
        (
            "scoring-blueprints-submission",
            (
                "Workflow that takes as user input a Github repo link "
                "and checks it against guidelines found at www.mozilla.ai/Bluerprints (check guidelines on developing top notch Blueprints). "
                "Then it should assess the submitted repo and give it a score out of 100. "
                "Finally the workflow should formulate the results with all necessary details in a suitable structured format "
                "and do BOTH of the following with it "
                "(1) post it to the blueprint-submission channel on Slack after finding the correct channel_id, and "
                "(2) log the entry to SQLite - to the already existing table named `github_repo_evaluations` in the `blueprints.db` database. "
                "Use the official MCP servers for Slack and SQLite and provide suitable MCP configurations "
                "along with only the necessary subset of tools required for the task at hand."
            ),
            40,
            420,
        ),
            # Agent with websearch tool and single MCP (Slack)
        (
            "slack-newsletter",
            (
(
                "Create a newsletter for my company about the latest AI news and trends. "
                "I need it to be based only on information from the following websites: "
                "https://www.anthropic.com/news "
                "https://news.mit.edu/topic/artificial-intelligence2 "
                "https://bair.berkeley.edu/blog/ "
                "https://deepmind.google/discover/blog/ "
                "The newsletter should only be based on new information from the last week. "
                "The newsletter should be structured into different sections. "
                "The total newsletter should be concise, with an informal tone, and less than 300 words total. "
                "Include links to relevant sources. "
                "The newsletter should be posted to the weekly-newsletter Slack channel."
)
            ),
            40,
            420,
        ),
        # Add new "use cases" here, following this format:
        # prompt_id: the directory where the artifacts will be generated under the /tests/assets folder
        # prompt: the actual prompt to pass for agent generation
        # expected_num_turns: the threshold max number of turns for the agent to complete the task
        # expected_execution_time: the threshold max execution time (in seconds) for the agent to complete the task
    ],
)
@pytest.mark.asyncio
async def test_single_turn_generation(
    tmp_path: Path,
    prompt_id: str,
    prompt: str,
    expected_num_turns: int,
    expected_execution_time: int,
    request: pytest.FixtureRequest,
):
    await single_turn_generation(user_prompt=prompt, output_dir=tmp_path)

    _assert_generated_files(tmp_path)

    # Verify the generated agent.py has valid Python syntax
    agent_file = tmp_path / "agent.py"
    _assert_agent_code_syntax(agent_file)
    _assert_agent_code_contains_trace_writing(agent_file)

    # Assertions based on manufacturing agent's trace
    agent_trace = load_agent_trace(tmp_path / "agent_factory_trace.json")
    _assert_execution_time_within_limit(agent_trace, expected_execution_time)
    _assert_num_turns_within_limit(agent_trace, expected_num_turns)

    # Assertions based on requirements.txt
    assert_requirements_first_line_matches_any_agent_version(tmp_path / "requirements.txt")
    assert_mcp_uv_consistency(tmp_path / "agent.py", tmp_path / "requirements.txt")
    assert_requirements_installable(tmp_path / "requirements.txt")

    update_artifacts = request.config.getoption("--update-artifacts")

    if update_artifacts:
        copytree(tmp_path, Path(__file__).parent.parent / "artifacts" / prompt_id, dirs_exist_ok=True)


@pytest.mark.asyncio
async def test_full_agent_generation_and_cost_tracking(tmp_path):
    # Actually run the agent factory and check costs are tracked
    user_prompt = "Create a simple agent that says hello"

    await single_turn_generation(user_prompt, output_dir=tmp_path)

    # Check all expected files exist with cost data
    assert (tmp_path / "agent_factory_trace.json").exists()
    assert (tmp_path / "agent.py").exists()

    # Verify trace has execution_costs
    trace_data = json.loads((tmp_path / "agent_factory_trace.json").read_text())
    assert "execution_costs" in trace_data
