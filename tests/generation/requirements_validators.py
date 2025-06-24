import re
import subprocess
import tempfile
from importlib.metadata import version
from pathlib import Path


def assert_requirements_first_line_matches_any_agent_version(requirements_path: Path):
    """Verify that the first line of requirements.txt matches any-agent[all]=={version}."""
    content = requirements_path.read_text(encoding="utf-8").strip()
    lines = content.split("\n")

    if not lines:
        raise AssertionError(f"requirements.txt is empty\n\nFull requirements.txt content:\n{content}")

    first_line = lines[0].strip()

    # Get the expected version from the installed any-agent package
    expected_version = version("any-agent")
    expected_first_line = f"any-agent[all]=={expected_version}"

    if first_line != expected_first_line:
        raise AssertionError(
            f"First line must be 'any-agent[all]=={expected_version}'. "
            f"Found: '{first_line}'\n\nFull requirements.txt content:\n{content}"
        )


def assert_mcp_uv_consistency(agent_file: Path, requirements_path: Path):
    """Verify MCP tool usage consistency with uv dependency."""
    agent_content = agent_file.read_text(encoding="utf-8")

    # Check for uvx usage using regex (looking for uvx command usage)
    uvx_pattern = r"uvx\s+"
    uvx_matches = re.findall(uvx_pattern, agent_content)
    has_uvx_usage = bool(uvx_matches)

    requirements_content = requirements_path.read_text(encoding="utf-8")
    requirements_lines = [line.strip() for line in requirements_content.split("\n") if line.strip()]

    # Check if 'uv' is in requirements
    has_uv_requirement = any(
        line.startswith("uv==") or line.startswith("uv>=") or line == "uv" for line in requirements_lines
    )

    debug_info = (
        f"\nDEBUG INFO:\n"
        f"- uvx_pattern: {uvx_pattern}\n"
        f"- uvx_matches found: {uvx_matches}\n"
        f"- has_uvx_usage: {has_uvx_usage}\n"
        f"- has_uv_requirement: {has_uv_requirement}\n\n"
        f"Full agent.py content:\n{agent_content}\n\n"
        f"Full requirements.txt content:\n{requirements_content}"
    )

    if has_uvx_usage and not has_uv_requirement:
        raise AssertionError(
            "Found uvx usage in agent.py but 'uv' is not present in requirements.txt. "
            "When using MCP tools with uvx, 'uv' must be included in requirements.txt" + debug_info
        )

    if not has_uvx_usage and has_uv_requirement:
        raise AssertionError(
            "Found 'uv' in requirements.txt but no uvx usage detected in agent.py. "
            "'uv' should only be present when MCP tools are used" + debug_info
        )


def assert_requirements_installable(requirements_path: Path, timeout: int = 180):
    """Verify that the requirements can be installed in a clean environment.

    Args:
        requirements_path: Path to the requirements.txt file
        timeout: Maximum time in seconds to wait for installation
    """
    # Read requirements content for debugging
    requirements_content = requirements_path.read_text(encoding="utf-8")

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
                f"Failed to install requirements:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}\n\n"
                f"Full requirements.txt content:\n{requirements_content}"
            )
        except subprocess.TimeoutExpired:
            raise AssertionError(
                f"Requirements installation timed out after {timeout} seconds\n\n"
                f"Full requirements.txt content:\n{requirements_content}"
            ) from None
        except subprocess.CalledProcessError as e:
            raise AssertionError(
                f"Failed to create virtual environment:\nSTDOUT: {e.stdout}\nSTDERR: {e.stderr}\n\n"
                f"Full requirements.txt content:\n{requirements_content}"
            ) from e
