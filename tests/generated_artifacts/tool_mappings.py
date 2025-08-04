from generated_artifacts.tool_mocks import mock_extract_text_from_url, mock_text_to_speech
from generated_artifacts.tool_validations import no_docker_mcp

from agent_factory.utils.logging import logger

# Each entry defines how to identify a tool and what mock to use
TOOL_MOCKS = [
    {
        "prompt_id": "url-to-podcast",  # mocks can be specific to a use-case (identified by its prompt_id)
        "type": "MCPStdio",  # Tool type: 'mcp' for MCPStdio tools, 'function' for regular functions
        "match_condition": "mcp/elevenlabs",  # String to match in tool args (for MCP) or function name (for functions)
        "mock_function": mock_text_to_speech,
    },
    {
        "prompt_id": "url-to-podcast",
        "type": "MCPStdio",
        "match_condition": "elevenlabs-mcp",  # this string appears as args of uvx MCP (previous one was docker)
        "mock_function": mock_text_to_speech,
    },
    {
        "prompt_id": "url-to-podcast",
        "type": "function",
        "match_condition": "extract_text_from_url",  # this string appears as function name
        "mock_function": mock_extract_text_from_url,
    },
]

# Each entry defines how to identify a tool and what validation to run on it.
# NOTE that these are conditions to be met by the original tools and they are
# verified prior to mocking.
TOOL_VALIDATIONS = [
    {
        # We found the docker MCP server was problematic for the url-to-podcast use-case
        # and decided to explicitly ask for the uvx installation in the instructions.
        # Here we make sure no docker tools are run in this use-case.
        "prompt_id": "url-to-podcast",
        "type": "MCPStdio",
        "validation_function": no_docker_mcp,
    }
]

# ----------------------------------------------------------------------------


def find_matching_validation(tool, tool_type_checker, prompt_id):
    """Find a matching validation for the given tool.

    Args:
        tool: The tool to check
        tool_type_checker: Function that takes (tool, type_name) and returns True if tool matches type

    Returns:
        Validation function if found, None otherwise
    """
    for val_config in TOOL_VALIDATIONS:
        tool_type = val_config["type"]
        match_prompt_id = val_config.get("prompt_id", None)

        if match_prompt_id and prompt_id != match_prompt_id:
            continue

        if tool_type_checker(tool, tool_type):
            logger.debug(f"Found matching validation function for {match_prompt_id}/{tool_type}")
            return val_config["validation_function"]

    return None


def find_matching_mock(tool, tool_type_checker, prompt_id):
    """Find a matching mock for the given tool.

    Args:
        tool: The tool to check
        tool_type_checker: Function that takes (tool, type_name) and returns True if tool matches type

    Returns:
        Mock function if found, None otherwise
    """
    for mock_config in TOOL_MOCKS:
        tool_type = mock_config["type"]
        match_condition = mock_config["match_condition"]
        match_prompt_id = mock_config.get("prompt_id", None)

        if match_prompt_id and prompt_id != match_prompt_id:
            continue

        if tool_type == "MCPStdio":
            # Check if it's an MCP tool with matching args
            if tool_type_checker(tool, tool_type) and any(match_condition in str(arg) for arg in tool.args):
                logger.debug(f"Found matching MCP mock for: {match_condition}")
                return mock_config["mock_function"]

        elif tool_type == "function":
            # Check if it's a function with matching name
            if tool_type_checker(tool, tool_type) and hasattr(tool, "__name__") and match_condition in tool.__name__:
                logger.debug(f"Found matching function mock for: {match_condition}")
                return mock_config["mock_function"]

    return None
