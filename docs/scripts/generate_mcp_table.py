#!/usr/bin/env python3
"""Generate MCP Servers Table

This script reads the test results JSON and generates the markdown table
for mcp-servers.md with current test status.
"""

import json
import re
from pathlib import Path
from typing import Any


def load_test_results(results_file: str = "docs/scripts/mcp-test-results.json") -> dict[str, Any]:
    """Load test results from JSON file."""
    with Path(results_file).open("r") as f:
        return json.load(f)


def get_status_display(test_status: str) -> tuple[str, str]:
    """Get status icon and text for display."""
    status_map = {
        "success": ("✅", "✅ Confirmed"),
        "skipped": ("⏭️", "⏭️ Skipped"),
        "failed": ("❌", "❌ Failed"),
    }
    return status_map.get(test_status, ("❌", "❌ Failed"))


def create_table_row(server_name: str, server_config: dict[str, Any]) -> str:
    """Create a single table row for a server."""
    test_status = server_config.get("test_status", "failed")
    status_icon, status_text = get_status_display(test_status)

    command = server_config["command"]
    args = server_config.get("args", [])
    command_str = f"`{command} {' '.join(args)}`"
    description = server_config.get("description", "")

    return f"| **{server_name.title()}** | {command_str} | stdio | {status_text} | {description} |"


def generate_table_content(servers: dict[str, Any]) -> str:
    """Generate the complete table content."""
    header = "| Server Name | Installation | Protocol | Status | Description |"
    separator = "| --- | --- | --- | --- | --- |"

    rows = [create_table_row(name, config) for name, config in servers.items()]

    return f"\n{header}\n{separator}\n" + "\n".join(rows)


def add_test_summary(content: str, test_data: dict[str, Any]) -> str:
    """Add test run summary to the content, replacing any existing summaries."""
    test_info = f"\n\n*Last updated: {test_data['test_run']['timestamp']}*  \n"
    test_info += (
        f"*Test results: {test_data['test_run']['successful']} working, "
        f"{test_data['test_run']['failed']} failed, {test_data['test_run']['skipped']} skipped "
        f"out of {test_data['test_run']['total_servers']} total servers*"
    )

    # Remove any existing test summary entries (lines starting with *Last updated:)
    # This pattern matches the entire block of test summary entries
    content = re.sub(
        r"\n\*Last updated:.*?\*\s*\n\*Test results:.*?\*\s*\n(\*Last updated:.*?\*\s*\n\*Test results:.*?\*\s*\n)*",
        "\n",
        content,
        flags=re.DOTALL,
    )

    # Add the new test summary at the beginning (after the title)
    return re.sub(r"(# MCP Servers\n)", r"\1" + test_info, content, count=1)


def update_markdown_file(
    markdown_file: str = "docs/mcp-servers.md", results_file: str = "docs/scripts/mcp-test-results.json"
):
    """Update the markdown file with the new table."""
    test_data = load_test_results(results_file)
    servers = test_data["mcpServers"]

    with Path(markdown_file).open("r") as f:
        content = f.read()

    # We are embedding the table, so we need these markers
    start_marker = "<!-- MCP_SERVERS_TABLE_START -->"
    end_marker = "<!-- MCP_SERVERS_TABLE_END -->"

    start_pos = content.find(start_marker)
    end_pos = content.find(end_marker)

    if start_pos == -1 or end_pos == -1:
        print("Could not find table markers in markdown file")
        return

    table_content = generate_table_content(servers)
    new_table = f"{start_marker}{table_content}\n{end_marker}"

    new_content = content[:start_pos] + new_table + content[end_pos + len(end_marker) :]

    new_content = add_test_summary(new_content, test_data)

    with Path(markdown_file).open("w") as f:
        f.write(new_content)

    test_run = test_data["test_run"]
    print(f"Updated {markdown_file} with test results")
    print(
        f"Test run: {test_run['successful']} working, {test_run['failed']} failed, "
        f"{test_run['skipped']} skipped out of {test_run['total_servers']} total servers"
    )


def main():
    """Main function."""
    update_markdown_file()


if __name__ == "__main__":
    main()
