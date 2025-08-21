import importlib
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from generated_artifacts.tool_mappings import find_matching_mock, find_matching_validation

from agent_factory.utils.logging import logger


@pytest.fixture
def generated_agent_module_with_mocks(agent_dir: Path, prompt_id: str):
    """Import the agent module dynamically with mocks in place"""
    logger.debug(f"Testing agent from: {agent_dir}")

    # if agent_dir does not exist, break early
    if not agent_dir.exists():
        raise AssertionError(f"Agent directory {agent_dir} does not exist.")

    # Add the agent directory to sys.path
    sys.path.insert(0, str(agent_dir))

    # Import the original method before patching
    from any_agent.frameworks.any_agent import AnyAgent

    original_load_tools = AnyAgent._load_tools

    async def mocking_load_tools(self, tools):
        """A version of AnyAgent's _load_tools that mocks tool calls.

        Parameters:
        - tools: a list of tools provided in the agent's configuration

        Returns:
        - a patched version of _load_tools' output, where some specific
          tools are mocked by those provided in `mock_tools.py`
        """
        logger.debug(f"AnyAgent._load_tools called with {len(tools)} tools:")
        for i, tool in enumerate(tools):
            logger.debug(f"    Tool {i}: {type(tool)} - {tool}")

        # Process tools and replace with mocks where applicable
        modified_tools = []
        for tool in tools:
            # first validate the tool
            validation_functions = find_matching_validation(tool, prompt_id)

            for validation_function in validation_functions:
                logger.debug(f"Validating tool {tool} with {validation_function.__name__}")
                validation_function(tool, prompt_id)

            # Try to find matching mocks:
            # - if function, there is a 1:1 mapping
            # - if MCPStdio, each tool under the same server needs to have a mock
            mock_tools = find_matching_mock(tool, prompt_id)

            if len(mock_tools):
                logger.debug(f"Replacing tool {tool} with: {[func.__name__ for func in mock_tools]}")
                modified_tools.extend(mock_tools)
            else:
                # No mock found, keep original tool
                modified_tools.append(tool)

        logger.debug(f"Modified tools count: {len(modified_tools)}")
        for i, tool in enumerate(modified_tools):
            logger.debug(f"  Tool {i}: {type(tool)} - {tool}")

        # Call original method with modified tools
        result = await original_load_tools(self, modified_tools)

        logger.debug(f"Original _load_tools returned: {len(result[0])} tools, {len(result[1])} mcp_servers")

        return result

    try:
        # Patch _load_tools before importing agent
        with patch.object(AnyAgent, "_load_tools", mocking_load_tools):
            logger.debug("Patched AnyAgent._load_tools")

            # Import the agent module
            if "agent" in sys.modules:
                importlib.reload(sys.modules["agent"])
            else:
                import agent

            logger.debug("Agent module imported successfully")

            yield agent

    finally:
        # Clean up
        sys.path.remove(str(agent_dir))
        if "agent" in sys.modules:
            del sys.modules["agent"]


@pytest.mark.artifact_integration
def test_agent_mocked_execution(generated_agent_module_with_mocks, prompt_id: str):
    """Test agent execution with _load_tools mocking"""
    agent = generated_agent_module_with_mocks

    logger.debug("Starting agent execution...")

    try:
        if "url-to-podcast" in prompt_id:
            result = agent.main("https://en.wikipedia.org/wiki/Alan_Turing_Life")

            # the agent completes with a file generated in the /tmp folder
            # NOTE that the field names here might change if you rebuild the agent!
            assert "/tmp" in result.podcast_path

        elif "scoring-blueprints-submission" in prompt_id:
            result = agent.main("https://github.com/mozilla-ai/surf-spot-finder")

            # the agent completes with the following conditions satisfied
            # NOTE that the field names here might change if you rebuild the agent!
            assert result.score  # the agent assigned a score
            assert result.slack_channel_id == "BLU3PR1NTSUB"  # the agent found the channel id
            assert result.slack_ts  # the agent posted in the channel
            assert result.db_insert_success  # the agent inserted results in the DB

        elif "summarize-url-content" in prompt_id:
            result = agent.main("https://en.wikipedia.org/wiki/Alan_Turing_Life")

            # # NOTE that the field names here might change if you rebuild the agent!
            assert "Turing" in result.summary  # the agent has built a summary of the page

        else:
            # we are not testing other use-cases atm, but we can expect they will be
            # called with different parameters so we'll have an if...elif...else here
            raise AssertionError(f"Prompt id `{prompt_id}` is not supported by this test")

        logger.debug(f"Agent execution completed with result: {type(result)}")

    except Exception as e:
        logger.error(f"Exception occurred: {type(e).__name__}: {e}")
        pytest.fail(f"Exception: {type(e).__name__}: {e}")

    assert result is not None
    logger.info(result)
