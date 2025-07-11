import re
import subprocess
from importlib.metadata import version
from pathlib import Path


def assert_requirements_first_line_matches_any_agent_version(requirements_path: Path):
    """Verify that the first line of requirements.txt matches any-agent[all,a2a]=={version}."""
    content = requirements_path.read_text(encoding="utf-8").strip()
    lines = content.split("\n")

    if not lines:
        raise AssertionError(f"requirements.txt is empty\n\nFull requirements.txt content:\n{content}")

    first_line = lines[0].strip()

    # Get the expected version from the installed any-agent package
    expected_version = version("any-agent")
    expected_first_line = f"any-agent[all,a2a]=={expected_version}"

    if first_line != expected_first_line:
        raise AssertionError(
            f"First line must be 'any-agent[all,a2a]=={expected_version}'. "
            f"Found: '{first_line}'\n\nFull requirements.txt content:\n{content}"
        )


def assert_mcp_uv_consistency(agent_file: Path, requirements_path: Path):
    """Verify MCP tool usage consistency with uv dependency."""
    agent_content = agent_file.read_text(encoding="utf-8")

    # Check for uvx usage using regex (looking for uvx command usage)
    uvx_pattern = r"uvx\s*"
    uvx_matches = re.findall(uvx_pattern, agent_content)
    uses_uvx = bool(uvx_matches)

    requirements_content = requirements_path.read_text(encoding="utf-8")
    requirements_lines = [line.strip() for line in requirements_content.split("\n") if line.strip()]

    # Check if 'uv' is in requirements
    requires_uvx = any(
        line.startswith("uv==") or line.startswith("uv>=") or line == "uv" for line in requirements_lines
    )

    debug_info = (
        f"\nDEBUG INFO:\n"
        f"- uvx_pattern: {uvx_pattern}\n"
        f"- uvx_matches found: {uvx_matches}\n"
        f"- uses_uvx: {uses_uvx}\n"
        f"- requires_uvx: {requires_uvx}\n\n"
        f"Full agent.py content:\n{agent_content}\n\n"
        f"Full requirements.txt content:\n{requirements_content}"
    )

    if uses_uvx and not requires_uvx:
        raise AssertionError(
            "Found uvx usage in agent.py but 'uv' is not present in requirements.txt. "
            "When using MCP tools with uvx, 'uv' must be included in requirements.txt" + debug_info
        )

    if not uses_uvx and requires_uvx:
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

    try:
        # Use uv run to install and test in a throwaway environment
        result = subprocess.run(
            ["uv", "run", "--with-requirements", str(requirements_path), "--python", "3.13", "python", "-V"],
            check=False,
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
