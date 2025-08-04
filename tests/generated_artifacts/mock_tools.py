import hashlib
import shutil
from pathlib import Path

from any_agent.config import MCPStdio

from agent_factory.utils.logging import logger

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
    logger.debug(f"Mock text_to_speech called with text: '{text[:50]}...', voice_name: {voice_name}")
    text_hash = hashlib.md5(text.encode("utf-8")).hexdigest()
    output_file = Path(f"/tmp/mock_audio_{text_hash}.mp3")
    input_file = Path(ARTIFACTS_PATH) / "silent_1000.mp3"

    # Check if file already exists (just log for internal use, but still return success)
    if output_file.exists():
        logger.warning(f"File already exists: {output_file}")
        return f"Success. File saved as: {output_file}. Voice used: {voice_name}"

    # Create a minimal valid MP3 file (silent audio, ~1 seconds)
    shutil.copy(input_file, output_file)
    logger.debug(f"Created mock MP3 file: {output_file}")

    return f"Success. File saved as: {output_file}. Voice used: {voice_name}"


def mock_extract_text_from_url(url: str) -> str:
    """Extracts all text content from a given URL.

    This function fetches the HTML content of the URL and uses BeautifulSoup
    to parse and extract all human-readable text.

    Args:
        url: The URL from which to extract text (e.g., "https://example.com").

    Returns:
        A string containing the extracted text. If an error occurs (e.g.,
        network issue, invalid URL), it returns an error message string.
    """
    url_hash = hashlib.md5(url.encode("utf-8")).hexdigest()
    content_file = Path(__file__).parent / "data" / f"{url_hash}.md"

    if content_file.exists():
        # Return file content
        return content_file.read_text()

    return "Error: URL not accessible"


# ----------------------------------------------------------------------------


def no_docker_mcp(MCPStdio_tool_config: MCPStdio, prompt_id: str):
    """Makes sure that MCPStdio tool is not running on docker."""
    assert "docker" not in MCPStdio_tool_config.command.lower(), f"Docker MCP cannot be used in {prompt_id}"


# ----------------------------------------------------------------------------

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
