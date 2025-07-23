import hashlib
import importlib
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from loguru import logger

ARTIFACTS_PATH = Path(__file__).parent.parent / "artifacts"


@pytest.fixture(
    # params=list(ARTIFACTS_PATH.rglob("*agent.py")),
    params=[x for x in list(ARTIFACTS_PATH.rglob("*agent.py")) if "podcast" in str(x)],
    ids=lambda x: x.parent.name,
)
def generated_agent_module_with_mocks(request: pytest.FixtureRequest):
    """Import the agent module dynamically with mocks in place"""
    agent_file = request.param
    agent_dir = agent_file.parent

    logger.info(f"Testing agent from: {agent_dir}")

    # Add the agent directory to sys.path
    sys.path.insert(0, str(agent_dir))

    # Import the original method before patching
    from any_agent.config import MCPStdio
    from any_agent.frameworks.any_agent import AnyAgent

    original_load_tools = AnyAgent._load_tools

    async def logging_load_tools(self, tools):
        logger.info(f"AnyAgent._load_tools called with {len(tools)} tools:")
        for i, tool in enumerate(tools):
            logger.info(f"    Tool {i}: {type(tool)} - {tool}")

        # Find and replace MCPStdio tools with mcp/elevenlabs in args
        modified_tools = []
        for tool in tools:
            if isinstance(tool, MCPStdio) and any("mcp/elevenlabs" in str(arg) for arg in tool.args):
                logger.info(f"Found ElevenLabs MCP tool: {tool}")

                # Create a mock function to replace it
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

                    # Check if file already exists
                    if output_file.exists():
                        logger.warning(f"File already exists: {output_file}")
                        return output_file

                    # Create a minimal valid MP3 file (silent audio, ~0.1 seconds)
                    # This is a minimal MP3 header for a silent audio file
                    minimal_mp3_data = bytes(
                        [
                            0xFF,
                            0xFB,
                            0x90,
                            0x00,  # MP3 header
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                            0x00,
                        ]
                    )

                    try:
                        # Write the minimal MP3 data to file
                        with output_file.open("wb") as f:
                            f.write(minimal_mp3_data)
                        logger.info(f"Created mock MP3 file: {output_file}")
                    except Exception as e:
                        logger.error(f"Failed to create MP3 file: {e}")
                        raise

                    return f"Success. File saved as: {output_file}. Voice used: {voice_name}"

                # Add the mock function with the right name
                mock_text_to_speech.__name__ = "text_to_speech"
                modified_tools.append(mock_text_to_speech)
                logger.info("Replaced ElevenLabs MCP with mock function")
                for i, tool in enumerate(modified_tools):
                    logger.info(f"  Tool {i}: {type(tool)} - {tool}")
            else:
                modified_tools.append(tool)

        # Call original method with modified tools
        result = await original_load_tools(self, modified_tools)

        logger.info(f"Original _load_tools returned: {len(result[0])} tools, {len(result[1])} mcp_servers")

        return result

    try:
        # Patch _load_tools before importing agent
        with patch.object(AnyAgent, "_load_tools", logging_load_tools) as mock_load_tools:
            logger.info("Patched AnyAgent._load_tools")

            # Import the agent module
            if "agent" in sys.modules:
                importlib.reload(sys.modules["agent"])
            else:
                import agent

            logger.info("Agent module imported successfully")

            yield agent, mock_load_tools

    finally:
        # Clean up
        sys.path.remove(str(agent_dir))
        if "agent" in sys.modules:
            del sys.modules["agent"]


def test_agent_mocked_execution(generated_agent_module_with_mocks):
    """Test agent execution with _load_tools logging"""
    agent, mock_load_tools = generated_agent_module_with_mocks

    logger.info("Starting agent execution...")

    try:
        result = agent.main("https://aittalam.github.io/posts/2023-12-31-setting-up-hugo/")
        logger.info(f"Agent execution completed with result: {type(result)}")

    except Exception as e:
        logger.error(f"Exception occurred: {type(e).__name__}: {e}")
        pytest.fail(f"Exception: {type(e).__name__}: {e}")

    assert result is not None
