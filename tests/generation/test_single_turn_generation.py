import ast
import subprocess
import tempfile
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


def _assert_requirements_installable(requirements_path: Path, timeout: int = 180):
    """Verify that the requirements can be installed in a clean environment.

    Args:
        requirements_path: Path to the requirements.txt file
        timeout: Maximum time in seconds to wait for installation
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        env_dir = Path(temp_dir) / ".venv"

        try:
            # Create a new virtual environment
            subprocess.run(
                ["uv", "venv", str(env_dir), "--python=python3.11"],
                check=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            # Install requirements
            result = subprocess.run(
                ["uv", "pip", "install", "-r", str(requirements_path)],
                check=False,
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            assert result.returncode == 0, (
                f"Failed to install requirements:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
            )
        except subprocess.TimeoutExpired:
            raise AssertionError(f"Requirements installation timed out after {timeout} seconds") from None
        except subprocess.CalledProcessError as e:
            raise AssertionError(
                f"Failed to create virtual environment:\nSTDOUT: {e.stdout}\nSTDERR: {e.stderr}"
            ) from e


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
def test_single_turn_generation(tmp_path: Path, prompt_id: str, prompt: str, request: pytest.FixtureRequest):
    single_turn_generation(user_prompt=prompt, output_dir=tmp_path)

    _assert_generated_files(tmp_path)

    # Verify the generated agent.py has valid Python syntax
    _assert_agent_syntax(tmp_path / "agent.py")

    # Verify requirements can be installed in a clean environment
    _assert_requirements_installable(tmp_path / "requirements.txt")

    update_artifacts = request.config.getoption("--update-artifacts")

    if update_artifacts:
        copytree(tmp_path, Path(__file__).parent.parent / "artifacts" / prompt_id, dirs_exist_ok=True)
