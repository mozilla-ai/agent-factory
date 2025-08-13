import hashlib
import shutil
import time
from pathlib import Path

from agent_factory.utils.logging import logger

# Path to artifacts directory (we don't use the one from conftest as
# we cannot change the mocks' interface by adding extra parameters)
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


def mock_slack_list_channels() -> str:
    """List public or pre-defined channels in the workspace."""
    return """
{
  "type": "text",
  "text": "{\"ok\":true,\"channels\":[
    {\"id\":\"G3N3R4LCH4NL\",\"name\":\"general\",\"is_channel\":true},
    {\"id\":\"BLU3PR1NTSUB\",\"name\":\"blueprint-submission\",\"is_channel\":true},
    {\"id\":\"BLU3PR1NTSC0\",\"name\":\"blueprint-scoring\",\"is_channel\":true},
    {\"id\":\"BLU3PR1NTG3N\",\"name\":\"blueprint-general\",\"is_channel\":true}
    ]}",
  "annotations": null,
  "meta": null
}
"""


def mock_slack_post_message(channel_id: str, text: str) -> str:
    """Post a new message to a Slack channel.

    Parameters:
    - channel_id: The ID of the channel to post to
    - text: The message text to post
    """
    ts = time.time()

    return f"""
{{
  "type": "text",
  "text": "{{\"ok\":true,\"channel\":\"{channel_id}\",\"ts\":\"{ts}\",\"message\":{{\"user\":\"M0CKUS3R\",\"type\":\"message\",\"ts\":\"{ts}\",\"bot_id\":\"M0CKB0T\",\"app_id\":\"M0CK4PP\",\"text\":\"{text}\"}}}}",
  "annotations": null,
  "meta": null
}}
"""


def mock_sqlite_write_query(query: str) -> str:
    """Execute an INSERT, UPDATE, or DELETE query on the SQLite database.

    Parameters:
    - query: SQL query to execute
    """
    logger.info(f"SQLite write_query got the following query: {query}")
    return """
{
  "type": "text",
  "text": "[{'affected_rows': 1}]",
  "annotations": null,
  "meta": null
}
"""
