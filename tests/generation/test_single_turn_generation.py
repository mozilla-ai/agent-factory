import ast
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from shutil import copytree

import pytest

from agent_factory.generation import single_turn_generation


def _assert_generated_files(workflow_dir: Path):
    existing_files = [f.name for f in workflow_dir.iterdir()]
    for expected_file in ["agent.py", "INSTRUCTIONS.md", "requirements.txt"]:
        assert expected_file in existing_files, f"{expected_file} was not generated."


def _assert_agent_syntax(agent_file: Path):
    ast.parse(agent_file.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    ("prompt_id", "prompt"),
    [
        (
            "url-to-podcast",
            "Create a workflow that takes an input web URL and creates an audio podcast with multiple speakers.",
        ),
        # Add new "use cases" here, following this format:
        # prompt_id: the directory where the artifacts will be generated under the /tests/assets folder
        # prompt: the actual prompt to pass for agent generation
    ],
)
def test_singe_turn_generation(tmp_path: Path, prompt_id: str, prompt: str, request: pytest.FixtureRequest):
    single_turn_generation(user_prompt=prompt, output_dir=tmp_path)

    _assert_generated_files(tmp_path)

    _assert_agent_syntax(tmp_path / "agent.py")

    update_assets = request.config.getoption("--update-assets")

    if update_assets:
        copytree(tmp_path, Path(__file__).parent.parent / "assets" / prompt_id, dirs_exist_ok=True)
