import ast
from pathlib import Path
from shutil import copytree

import pytest
from requirements_validators import (
    assert_mcp_uv_consistency,
    assert_requirements_first_line_matches_any_agent_version,
    assert_requirements_installable,
)
from utils.non_deterministic_runs import run_until_success_threshold_async

from agent_factory.agent_generator import generate_target_agent
from agent_factory.utils.client_utils import is_server_live


def _assert_generated_files(workflow_dir: Path, requires_mcpd: bool):
    """Makes sure all and only the expected files are generated for each agent.

    Every agent has a set of expected_files. Only those agents requiring mcpd
    have a few extra ones. (NOTE: .gitignore is currently always present even
    if agents which don't require mcpd don't need it).

    Parameters:
    - workflow_dir: the directory where the agent resides
    - requires_mcpd: a parameter specifying whether the agent requires
      mcpd to work (this information is stored in `use_cases.yaml`)
    """
    existing_files = [f.name for f in workflow_dir.iterdir() if not f.is_dir()]
    expected_files = [
        ".gitignore",
        "agent.py",
        "README.md",
        "requirements.txt",
        "agent_parameters.json",
        "agent_factory_trace.json",
    ]
    if requires_mcpd:
        expected_files.extend([".env", ".mcpd.toml", "secrets.prod.toml"])

    for expected_file in expected_files:
        assert expected_file in existing_files, f"{expected_file} was not generated."

    assert set(existing_files) == set(expected_files), (
        f"Extra files were generated: {set(existing_files) - set(expected_files)}"
    )


def _assert_agent_code_syntax(agent_file: Path):
    ast.parse(agent_file.read_text(encoding="utf-8"))


@pytest.mark.asyncio
@run_until_success_threshold_async()
async def test_single_turn_generation(
    tmp_path: Path,
    request: pytest.FixtureRequest,
    use_cases: dict,
    requires_mcpd: bool,
    max_attempts: int,
    min_successes: int,
):
    """Test the generation of a single turn agent and validate the generated artifacts.

    This test generates an agent based on the provided prompt and then runs validation
    tests on the generated artifacts.
    """
    # Get the prompt_id from command line or use default
    prompt_id = request.config.getoption("--prompt-id")

    if prompt_id not in use_cases:
        pytest.fail(f"Prompt ID '{prompt_id}' not found in test cases. Available IDs: {list(use_cases.keys())}")

    test_case = use_cases[prompt_id]

    assert is_server_live("localhost", 8080), "Agent server is not live on localhost:8080"
    full_path = tmp_path / prompt_id
    await generate_target_agent(message=test_case["prompt"], output_dir=full_path)

    # Verify the expected files were generated
    _assert_generated_files(full_path, requires_mcpd)

    # Verify the generated agent.py has valid Python syntax
    agent_file = full_path / "agent.py"
    _assert_agent_code_syntax(agent_file)

    # Assertions based on requirements.txt
    assert_requirements_first_line_matches_any_agent_version(full_path / "requirements.txt")
    assert_mcp_uv_consistency(full_path / "agent.py", full_path / "requirements.txt")
    assert_requirements_installable(full_path / "requirements.txt")

    update_artifacts = request.config.getoption("--update-artifacts")
    if update_artifacts:
        copytree(full_path, Path(__file__).parent.parent / "artifacts" / prompt_id, dirs_exist_ok=True)
