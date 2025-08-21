from generated_artifacts.tool_mocks import (
    mock_combine_mp3_files_for_podcast,
    mock_extract_text_from_url,
    mock_slack_list_channels,
    mock_slack_post_message,
    mock_sqlite_write_query,
    mock_text_to_speech,
)

from agent_factory.utils.logging import logger

# Each entry defines how to identify a tool and what mock to use
TOOL_MOCKS = [
    {
        # mocks can be specific to a use-case (identified by its prompt_id)
        "prompt_id": "url-to-podcast",
        # check if the function_name string appears in the function name
        # (the typical format is mcpservername__functionname, but one could
        # also specify a string that matches more than one tool and mock all
        # of them with the same function)
        "function_name": "elevenlabs_mcp__text_to_speech",
        # this is the mock we substitute the matched function with
        # (defined in `tool_mocks.py`)
        "mock_function": mock_text_to_speech,
    },
    {
        "prompt_id": "url-to-podcast",
        "function_name": "extract_text_from_url",
        "mock_function": mock_extract_text_from_url,
    },
    {
        "prompt_id": "url-to-podcast",
        "function_name": "combine_mp3_files_for_podcast",
        "mock_function": mock_combine_mp3_files_for_podcast,
    },
    {
        "prompt_id": "scoring-blueprints-submission",
        "function_name": "slack__slack_list_channels",
        "mock_function": mock_slack_list_channels,
    },
    {
        "prompt_id": "scoring-blueprints-submission",
        "function_name": "slack__slack_post_message",
        "mock_function": mock_slack_post_message,
    },
    {
        "prompt_id": "scoring-blueprints-submission",
        "function_name": "sqlite__write_query",
        "mock_function": mock_sqlite_write_query,
    },
    {
        "prompt_id": "summarize-url-content",
        "function_name": "extract_text_from_url",
        "mock_function": mock_extract_text_from_url,
    },
]

# ----------------------------------------------------------------------------


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
    # as we match the mock to (a substring of) the function name, we expect the function to have one
    if callable(tool) and hasattr(tool, "__name__"):
        for mock_config in mocks_for_this_prompt:
            if mock_config["function_name"] in tool.__name__:
                logger.debug(f"Found matching function mock for: {tool.__name__}")
                mocks.append(mock_config["mock_function"])

    return mocks
