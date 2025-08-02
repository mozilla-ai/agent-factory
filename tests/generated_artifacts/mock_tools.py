import hashlib
import shutil
from pathlib import Path

from loguru import logger

# Path to artifacts directory (adjust as needed)
ARTIFACTS_PATH = Path(__file__).parent.parent / "artifacts"


def mock_text_to_speech(text: str, voice_name: str = None) -> str:
    """Mocks elevenlab's text_to_speech tool with a smaller amount of parameters as not all are needed.

    Original description:
    Convert text to speech with a given voice and save the output audio file to a given directory.
    Directory is optional, if not provided, the output file will be saved to $HOME/Desktop.
    Only one of voice_id or voice_name can be provided. If none are provided, the default voice will be used.

    Args:
      text (str): The text to convert to speech.
      voice_name (str, optional): The name of the voice to use.

    Returns:
      Text content with the path to the output file and name of the voice used.
    """
    logger.info(f"Mock text_to_speech called with text: '{text[:50]}...', voice_name: {voice_name}")
    text_hash = hashlib.md5(text.encode("utf-8")).hexdigest()
    output_file = Path(f"/tmp/mock_audio_{text_hash}.mp3")
    input_file = Path(ARTIFACTS_PATH) / "silent_1000.mp3"

    # Check if file already exists (just log for internal use, but still return success)
    if output_file.exists():
        logger.warning(f"File already exists: {output_file}")
        return f"Success. File saved as: {output_file}. Voice used: {voice_name}"

    # Create a minimal valid MP3 file (silent audio, ~1 seconds)
    shutil.copy(input_file, output_file)
    logger.info(f"Created mock MP3 file: {output_file}")

    return f"Success. File saved as: {output_file}. Voice used: {voice_name}"


# ----------------------------------------------------------------------------

# Tool matching configuration
# Each entry defines how to identify a tool and what mock to use
TOOL_MOCKS = [
    {
        "type": "MCPStdio",  # Tool type: 'mcp' for MCPStdio tools, 'function' for regular functions
        "match_condition": "mcp/elevenlabs",  # String to match in tool args (for MCP) or function name (for functions)
        "mock_function": mock_text_to_speech,
    },
    {
        "type": "MCPStdio",
        "match_condition": "elevenlabs-mcp",  # this string appears as args of uvx MCP (previous one was docker)
        "mock_function": mock_text_to_speech,
    },
]

# ----------------------------------------------------------------------------


def find_matching_mock(tool, tool_type_checker):
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

        if tool_type == "MCPStdio":
            # Check if it's an MCP tool with matching args
            if tool_type_checker(tool, tool_type) and any(match_condition in str(arg) for arg in tool.args):
                logger.info(f"Found matching MCP mock for: {match_condition}")
                return mock_config["mock_function"]

        elif tool_type == "function":
            # Check if it's a function with matching name
            if tool_type_checker(tool, tool_type) and hasattr(tool, "__name__") and match_condition in tool.__name__:
                logger.info(f"Found matching function mock for: {match_condition}")
                return mock_config["mock_function"]

    return None
