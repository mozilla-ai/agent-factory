from any_agent.config import MCPStdio
from generated_artifacts.tool_mocks import (
    mock_extract_text_from_url,
    mock_slack_list_channels,
    mock_slack_post_message,
    mock_sqlite_write_query,
    mock_text_to_speech,
)
from generated_artifacts.tool_validations import no_docker_mcp

from agent_factory.utils.logging import logger

# Each entry defines how to identify a tool and what mock to use
TOOL_MOCKS = [
    {
        "prompt_id": "url-to-podcast",  # mocks can be specific to a use-case (identified by its prompt_id)
        "type": "function",  # Tool type: 'mcp' for MCPStdio tools, 'function' for regular functions
        "match_condition": {
            "name": "elevenlabs_mcp__text_to_speech",  # this string appears in the function name
        },
        "mock_function": mock_text_to_speech,
    },
    {
        "prompt_id": "url-to-podcast",
        "type": "function",
        "match_condition": {
            "name": "extract_text_from_url",  # this string appears in the function name
        },
        "mock_function": mock_extract_text_from_url,
    },
    {
        "prompt_id": "scoring-blueprints-submission",
        "type": "function",
        "match_condition": {
            "name": "slack__slack_list_channels",  # this string appears in the function name
        },
        "mock_function": mock_slack_list_channels,
    },
    {
        "prompt_id": "scoring-blueprints-submission",
        "type": "function",
        "match_condition": {
            "name": "slack__slack_post_message",  # this string appears in the function name
        },
        "mock_function": mock_slack_post_message,
    },
    {
        "prompt_id": "scoring-blueprints-submission",
        "type": "function",
        "match_condition": {
            "name": "sqlite__write_query",  # this string appears in the function name
        },
        "mock_function": mock_sqlite_write_query,
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


def find_matching_validation(tool, prompt_id):
    """Find a matching validation for the given tool.

    Args:
        tool: The tool to check
        prompt_id: The prompt_id used to filter matching configurations

    Returns:
        List of validation functions if found, None otherwise
    """
    vals_for_this_prompt = [
        mock_config
        for mock_config in TOOL_VALIDATIONS
        if not mock_config.get("prompt_id", None) or mock_config.get("prompt_id") == prompt_id
    ]

    vals = []
    if isinstance(tool, MCPStdio):
        filtered_vals = [val for val in vals_for_this_prompt if val["type"] == "MCPStdio"]
        for val_config in filtered_vals:
            logger.debug(f"Found matching validation function for {prompt_id}/{val_config['type']}")
            vals.append(val_config["validation_function"])

    elif callable(tool) and hasattr(tool, "__name__"):
        filtered_vals = [val for val in vals_for_this_prompt if val["type"] == "function"]
        for val_config in filtered_vals:
            logger.debug(f"Found matching validation function for {prompt_id}/{val_config['type']}")
            vals.append(val_config["validation_function"])

    return vals


def find_matching_mock(tool, prompt_id):
    """Find a matching mock for the given tool.

    Args:
        tool: The tool to check
        prompt_id: The prompt_id used to filter matching configurations

    Returns:
        List of mock functions if found, None otherwise
    """
    mocks_for_this_prompt = [
        mock_config
        for mock_config in TOOL_MOCKS
        if not mock_config.get("prompt_id", None) or mock_config.get("prompt_id") == prompt_id
    ]

    mocks = []
    if isinstance(tool, MCPStdio):
        # if the tool is an MCPStdio server, iterate on its tools and
        # try to match each of them with the available mocks
        filtered_tool_mocks = [mock for mock in mocks_for_this_prompt if mock["type"] == "MCPStdio"]

        for mcp_tool in tool.tools:
            for mock_config in filtered_tool_mocks:
                match_condition = mock_config["match_condition"]

                if any(match_condition["args"] in str(arg) for arg in tool.args) and match_condition["tools"] in str(
                    mcp_tool
                ):
                    logger.debug(f"Found matching MCP mock for: {match_condition}")
                    mocks.append(mock_config["mock_function"])

    # as we match the mock to (a substring of) the function name, we expect the function to have one
    elif callable(tool) and hasattr(tool, "__name__"):
        filtered_tool_mocks = [mock for mock in mocks_for_this_prompt if mock["type"] == "function"]
        for mock_config in filtered_tool_mocks:
            match_condition = mock_config["match_condition"]
            if match_condition["name"] in tool.__name__:
                logger.debug(f"Found matching function mock for: {match_condition}")
                mocks.append(mock_config["mock_function"])

    return mocks
