#!/usr/bin/env python3
"""MCP Server Test Runner

This script tests all MCP servers from mcp-servers.json and generates a results JSON
with the same structure plus test status information.
"""

import asyncio
import json
import os
import shutil
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Configuration constants
INITIALIZE_TIMEOUT = 30  # seconds
LIST_TOOLS_TIMEOUT = 30  # seconds


def load_mcp_servers() -> dict[str, Any]:
    """Load MCP servers from JSON file."""
    json_path = Path("docs/mcp-servers.json")
    with json_path.open() as f:
        data = json.load(f)
    return data["mcpServers"]


@contextmanager
def temporary_env_vars(env_vars: dict[str, str]):
    """Context manager to temporarily set environment variables."""
    original_values = {}
    try:
        for key, value in env_vars.items():
            original_values[key] = os.environ.get(key)
            os.environ[key] = value
        yield
    finally:
        for key, original_value in original_values.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value


async def test_server(server_name: str, server_config: dict[str, Any]) -> dict[str, Any]:
    """Test a single MCP server and return results."""
    print(f"🔍 Testing {server_name}...")

    # Start with the original server config
    # And add test result fields, for the output json file that will feed the markdown table
    result = server_config.copy()
    result["test_status"] = "failed"  # "success", "failed", or "skipped"
    result["test_error"] = None
    result["tools_count"] = 0
    result["tested_at"] = datetime.now(UTC).isoformat()

    # Skip Docker-based servers - TODO: add a streamable http test
    if server_config["command"] == "docker":
        result["test_status"] = "skipped"
        result["test_error"] = "Docker-based servers skipped in CI environment"
        print("  ⏭️  Skipping Docker-based server")
        return result

    env_vars = {}
    if "env" in server_config:
        for env_var, _ in server_config["env"].items():
            if not os.getenv(env_var):
                env_vars[env_var] = f"fake_{env_var.lower()}"
                print(f"  🔧 Setting fake {env_var}")

    server_params = StdioServerParameters(
        command=server_config["command"], args=server_config["args"], env=server_config.get("env", {})
    )

    try:
        with temporary_env_vars(env_vars):
            print(f"  🔄 Connecting to {server_name}...")
            async with stdio_client(server_params) as streams:
                async with ClientSession(*streams) as session:
                    print(f"  🔄 Initializing {server_name}...")
                    await asyncio.wait_for(session.initialize(), timeout=INITIALIZE_TIMEOUT)

                    print(f"  🔄 Listing tools for {server_name}...")
                    response = await asyncio.wait_for(session.list_tools(), timeout=LIST_TOOLS_TIMEOUT)
                    tools = response.tools
                    result["test_status"] = "success"
                    result["tools_count"] = len(tools)
                    print(f"  ✅ {server_name}: Found {len(tools)} tools")

    except TimeoutError:
        result["test_status"] = "failed"
        result["test_error"] = f"Timeout after {INITIALIZE_TIMEOUT + LIST_TOOLS_TIMEOUT} seconds"
        print(f"  ⏰ {server_name}: Timeout - server unresponsive")
    except Exception as e:
        result["test_status"] = "failed"
        result["test_error"] = str(e)
        print(f"  ❌ {server_name}: Failed - {str(e)}")

    return result


async def run_all_tests() -> dict[str, Any]:
    """Run tests for all MCP servers and return results in the same structure as input."""
    servers = load_mcp_servers()

    print("MCP Server Testing")
    print("=" * 50)
    print(f"Testing {len(servers)} servers sequentially")
    print(f"Timeouts: Initialize={INITIALIZE_TIMEOUT}s, ListTools={LIST_TOOLS_TIMEOUT}s")
    print()

    results = {}
    for server_name, server_config in servers.items():
        result = await test_server(server_name, server_config)
        results[server_name] = result

    return results


def save_results(results: dict[str, Any], output_file: str = "docs/scripts/mcp-test-results.json"):
    """Save test results to JSON file with the same structure as input plus test data."""
    output_data = {
        "mcpServers": results,
        "test_run": {
            "timestamp": datetime.now(UTC).isoformat(),
            "total_servers": len(results),
            "successful": sum(1 for r in results.values() if r["test_status"] == "success"),
            "failed": sum(1 for r in results.values() if r["test_status"] == "failed"),
            "skipped": sum(1 for r in results.values() if r["test_status"] == "skipped"),
            "timeouts": {
                "initialize": INITIALIZE_TIMEOUT,
                "list_tools": LIST_TOOLS_TIMEOUT,
            },
        },
    }

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with Path(output_file).open("w") as f:
        json.dump(output_data, f, indent=2)

    print("\n📊 Results Summary:")
    print(f"  📁 Results saved to {output_file}")
    print(f"  📈 Total servers: {len(results)}")
    print(f"  ✅ Successful: {output_data['test_run']['successful']}")
    print(f"  ❌ Failed: {output_data['test_run']['failed']}")
    print(f"  ⏭️  Skipped: {output_data['test_run']['skipped']}")


async def main():
    """Main function to run all tests and save results."""
    # Some MCP servers need vaults (e.g. mcp-obsidian)
    test_vault = Path("test-vault")
    if not test_vault.exists():
        test_vault.mkdir()

    try:
        results = await run_all_tests()
        save_results(results)
    finally:
        if test_vault.exists():
            shutil.rmtree(test_vault)


if __name__ == "__main__":
    asyncio.run(main())
