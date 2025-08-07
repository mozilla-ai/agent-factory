#!/usr/bin/env python3
"""Generate MCP Registry

This script reads the test results JSON and generates the MCP registry JSON
file according to the Mozilla AI MCP Registry schema.
"""

import json
from pathlib import Path
from typing import Any

from jsonschema import ValidationError, validate
from loguru import logger

from . import TestStatus


def load_test_results(results_file: str = ".cache/mcp-test-results.json") -> dict[str, Any]:
    """Load test results from JSON file."""
    with Path(results_file).open() as f:
        return json.load(f)


def validate_registry_schema(
    registry: dict[str, Any], schema_path: str | Path = "docs/scripts/input/registry-schema.json"
) -> bool:
    """Validate that the generated registry follows the required schema."""
    schema_path = Path(schema_path)

    if not schema_path.exists():
        logger.warning(f"⚠️  Schema file not found at {schema_path}, skipping validation")
        return False

    try:
        with schema_path.open() as f:
            schema = json.load(f)

        validate(instance=registry, schema=schema)
        logger.info("✅ Registry validation passed")
        return True

    except ValidationError as e:
        logger.error(f"❌ Registry validation failed: {e.message}")
        return False
    except (json.JSONDecodeError, OSError) as e:
        logger.error(f"❌ Failed to load schema file: {e}")
        return False


def generate_mcp_registry(results: dict[str, Any]) -> dict[str, Any]:
    """Generate MCP registry JSON for successful servers according to Mozilla AI schema."""
    registry = {}

    for server_name, result in results.items():
        # MCPD has no use for failing MCPs, we are not documenting here (as opposed to the other script)
        if result["test_status"] != TestStatus.SUCCESS.value:
            continue

        command = result.get("command", "")
        if command == "npx":
            install_type = "npx"
        elif command == "uvx":
            install_type = "uvx"
        else:
            # only while mcpd does not support docker
            continue

        # See registry-schema.json
        server_info = {
            "id": server_name,
            "name": server_name,
            "description": result.get("description", ""),
            "license": "",  # Required but cannot determine
            "tools": result.get("tools", []),
            "installations": {
                "default": {
                    "type": install_type,
                    "command": command,
                    "version": "",  # Required but cannot determine
                    "recommended": False,
                    "deprecated": False,
                }
            },
            "isOfficial": False,  # default - we do not get this info from the MCP server
            "deprecated": False,  # default - we do not get this info from the MCP server
        }

        registry[server_name] = server_info

    return registry


def generate_registry(
    results_file: str = ".cache/mcp-test-results.json",
    output_file: str = "docs/assets/custom-registry.json",
):
    """Generate the MCP registry JSON file from test results."""
    try:
        test_data = load_test_results(results_file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"❌ Failed to load test results: {e}")
        return

    registry = generate_mcp_registry(test_data["mcpServers"])

    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    with Path(output_file).open("w") as f:
        json.dump(registry, f, indent=2)
        f.write("\n")  # Ensure newline at end of file

    logger.info(f"📋 MCP registry saved to {output_file}")
    logger.info(f"📝 Included {len(registry)} successful servers in registry")

    validate_registry_schema(registry)

    test_run = test_data["test_run"]
    logger.info("\n📊 Test Summary:")
    logger.info(f"  Total servers: {test_run['total_servers']}")
    logger.info(f"  Successful: {test_run['successful']}")
    logger.info(f"  Failed: {test_run['failed']}")
    logger.info(f"  Skipped: {test_run['skipped']}")
    logger.info(f"  Included in registry: {len(registry)}")


if __name__ == "__main__":
    generate_registry()
