import ast
import subprocess
import tempfile
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from shutil import copytree

import pytest
from requirements_validators import (
    assert_mcp_uv_consistency,
    assert_requirements_first_line_matches_any_agent_version,
    assert_requirements_installable,
)

from agent_factory.generation import single_turn_generation


def _assert_generated_files(workflow_dir: Path):
    existing_files = [f.name for f in workflow_dir.iterdir()]
    expected_files = ["agent.py", "INSTRUCTIONS.md", "requirements.txt", "agent_factory_trace.json"]

    for expected_file in expected_files:
        assert expected_file in existing_files, f"{expected_file} was not generated."

    extra_python_files = [f for f in existing_files if f.endswith(".py") and f != "agent.py"]
    assert len(extra_python_files) == 0, (
        f"Unexpected Python files found: {extra_python_files}. Only 'agent.py' should be generated."
    )


def _assert_agent_syntax(agent_file: Path):
    ast.parse(agent_file.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    ("prompt_id", "prompt"),
    [
        # Agent with no MCP tools needed
        (
            "summarize-url-content",
            "Create a workflow that takes an input web URL and returns a summary of the content. Do not use MCP servers for tools.",
        ),
        # Agent with MCP tools such as ElevenLabs
        (
            "url-to-podcast",
            "Create a workflow that takes an input web URL and creates an audio podcast with multiple speakers. Use ElevenLabs for text-to-speech.",
        ),
        # Add new "use cases" here, following this format:
        # prompt_id: the directory where the artifacts will be generated under the /tests/assets folder
        # prompt: the actual prompt to pass for agent generation
    ],
)
def test_single_turn_generation(tmp_path: Path, prompt_id: str, prompt: str, request: pytest.FixtureRequest):
    single_turn_generation(user_prompt=prompt, output_dir=tmp_path)

    _assert_generated_files(tmp_path)

    # Verify the generated agent.py has valid Python syntax
    _assert_agent_syntax(tmp_path / "agent.py")

    # Verify requirements.txt format (first line should be any-agent[all]==version)
    assert_requirements_first_line_matches_any_agent_version(tmp_path / "requirements.txt")

    # Verify MCP tool usage consistency with uv dependency
    assert_mcp_uv_consistency(tmp_path / "agent.py", tmp_path / "requirements.txt")

    # Verify requirements can be installed in a clean environment
    assert_requirements_installable(tmp_path / "requirements.txt")

    update_artifacts = request.config.getoption("--update-artifacts")

    if update_artifacts:
        copytree(tmp_path, Path(__file__).parent.parent / "artifacts" / prompt_id, dirs_exist_ok=True)
