import logging

import requests

logger = logging.getLogger(__name__)

DEFAUTL_MCP_URL = "https://raw.githubusercontent.com/pathintegral-institute/mcpm.sh/refs/heads/main/mcp-registry/servers/{0}.json"


def get_mcp_info(mcp_name: str) -> dict:
    """Get information about a specific MCP Server by its name.

    Get detailed information about a specific MCP Server by its name, including its description,
    configuration, and tools available.

    Args:
        mcp_name (str): The name of the MCP.

    Returns:
        dict: A dictionary containing the MCP information.
    """
    url = DEFAUTL_MCP_URL.format(mcp_name)
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error fetching MCP info: {e}")
        return {}
    except ValueError as e:
        logger.error(f"Error parsing JSON response: {e}")
        return {}


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python tools.py <mcp_name>")
        sys.exit(1)

    mcp_name = sys.argv[1]
    mcp_info = get_mcp_info(mcp_name)
    if mcp_info:
        print(f"MCP Info for {mcp_name}:")
        print(mcp_info)
    else:
        print(f"No information found for MCP: {mcp_name}")
