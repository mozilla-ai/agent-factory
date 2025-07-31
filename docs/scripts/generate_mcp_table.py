#!/usr/bin/env python3
"""Generate MCP Servers Table

This script reads the test results JSON and generates the markdown table
for mcp-servers.md with current test status.
"""

import json
from enum import Enum
from pathlib import Path
from typing import Any


class TestStatus(Enum):
    """Enum for MCP server test status values."""

    SUCCESS = "success"
    SKIPPED = "skipped"
    FAILED = "failed"


# Markers for identifying the dynamic content
START_MARKER = "<!-- MCP_SERVERS_TABLE_START -->"
END_MARKER = "<!-- MCP_SERVERS_TABLE_END -->"


def load_test_results(results_file: str = "docs/scripts/mcp-test-results.json") -> dict[str, Any]:
    """Load test results from JSON file."""
    with Path(results_file).open("r") as f:
        return json.load(f)


def create_table_row(server_name: str, server_config: dict[str, Any]) -> str:
    """Create a single table row for a server."""
    status_map = {
        TestStatus.SUCCESS.value: "✅ Confirmed",
        TestStatus.SKIPPED.value: "⏭️ Skipped",
        TestStatus.FAILED.value: "❌ Failed",
    }

    test_status = server_config.get("test_status", "failed")
    status_display = status_map.get(test_status, "❌ Failed")

    command = server_config.get("command", "")
    args = server_config.get("args", [])
    command_str = f"`{command} {' '.join(args)}`" if command else "*No command*"
    description = server_config.get("description", "")

    return f"| **{server_name.title()}** | {command_str} | stdio | {status_display} | {description} |"


def generate_table_content(servers: dict[str, Any]) -> str:
    """Generate the complete table content."""
    header = "| Server Name | Installation | Protocol | Status | Description |"
    separator = "| --- | --- | --- | --- | --- |"

    rows = [create_table_row(name, config) for name, config in servers.items() if config.get("command")]

    return f"{header}\n{separator}\n" + "\n".join(rows) if rows else "*No servers configured*"


def generate_dynamic_content(test_data: dict[str, Any]) -> str:
    """Generate the dynamic content that goes between the markers."""
    # Generate test summary
    test_info = f"\n\n*Last updated: {test_data['test_run']['timestamp']}*\n"
    test_info += (
        f"*Test results: {test_data['test_run']['successful']} working, "
        f"{test_data['test_run']['failed']} failed, {test_data['test_run']['skipped']} skipped "
        f"out of {test_data['test_run']['total_servers']} total servers*\n\n"
    )

    servers = test_data["mcpServers"]
    table_content = generate_table_content(servers)

    return test_info + table_content + "\n"


def extract_static_file_sections(content: str) -> tuple[str, str]:
    """Extract intro and outro from the markdown file.

    Returns:
        tuple: (intro, outro)
        - intro: everything before the start marker
        - outro: everything after the end marker
    """
    start_pos = content.find(START_MARKER)
    end_pos = content.find(END_MARKER)

    if start_pos == -1 or end_pos == -1:
        raise ValueError("Could not find table markers in markdown file")

    intro = content[:start_pos]
    outro = content[end_pos + len(END_MARKER) :]

    return intro, outro


def reconstruct_file(intro: str, dynamic_content: str, outro: str) -> str:
    """Reconstruct the markdown file from its three sections."""
    return intro + START_MARKER + dynamic_content + END_MARKER + outro


def update_markdown_file(
    markdown_file: str = "docs/mcp-servers.md", results_file: str = "docs/scripts/mcp-test-results.json"
):
    """Update the markdown file with new test results."""
    test_data = load_test_results(results_file)

    with Path(markdown_file).open("r") as f:
        content = f.read()

    try:
        # We now have a static section before the marker and another after the end marker - we reuse all
        # this from the existing file. There is only one part that needs to be generated and placed between
        # the two markers.
        intro, outro = extract_static_file_sections(content)
    except ValueError as e:
        print(f"Error: {e}")
        return

    # Generate new content from the static text we rescued and the dynamic one from the tests.
    new_dynamic_content = generate_dynamic_content(test_data)
    new_content = reconstruct_file(intro, new_dynamic_content, outro)

    with Path(markdown_file).open("w") as f:
        f.write(new_content)

    test_run = test_data["test_run"]
    print(f"Updated {markdown_file} with test results")
    print(
        f"Test run: {test_run['successful']} working, {test_run['failed']} failed, "
        f"{test_run['skipped']} skipped out of {test_run['total_servers']} total servers"
    )


if __name__ == "__main__":
    update_markdown_file()
