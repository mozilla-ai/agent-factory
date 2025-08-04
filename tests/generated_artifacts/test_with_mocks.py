import importlib
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from generated_artifacts.tool_mappings import find_matching_mock, find_matching_validation

from agent_factory.utils.logging import logger


@pytest.fixture
def generated_agent_module_with_mocks(agent_dir: str, prompt_id: str):
    """Import the agent module dynamically with mocks in place"""
    logger.debug(f"Testing agent from: {agent_dir}")

    # Add the agent directory to sys.path
    sys.path.insert(0, str(agent_dir))

    # Import the original method before patching
    from any_agent.config import MCPStdio
    from any_agent.frameworks.any_agent import AnyAgent

    original_load_tools = AnyAgent._load_tools

    def tool_type_checker(tool: any, type_name: str) -> bool:
        """Check if a tool matches a given type (specified as a string).

        Parameters:
        - tool: one of the tools defined in the agent configuration
        - type_name: MCPStdio or function

        Returns:
        - bool: whether the tool matches the type and satisfies
                some type-related checks
        """
        if type_name == "MCPStdio":
            return isinstance(tool, MCPStdio)
        elif type_name == "function":
            # as we match the mock to (a substring of) the function name,
            # we expect the function to have one
            return callable(tool) and hasattr(tool, "__name__")
        return False

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
            validation_function = find_matching_validation(tool, tool_type_checker, prompt_id)

            if validation_function:
                logger.debug(f"Validating tool {tool} with {validation_function.__name__}")
                validation_function(tool, prompt_id)

            # Try to find a matching mock
            mock_function = find_matching_mock(tool, tool_type_checker, prompt_id)

            if mock_function:
                logger.debug(f"Replacing tool {tool} with mock {mock_function.__name__}")
                modified_tools.append(mock_function)
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


def test_agent_mocked_execution(generated_agent_module_with_mocks, prompt_id: str):
    """Test agent execution with _load_tools mocking"""
    agent = generated_agent_module_with_mocks

    logger.debug("Starting agent execution...")

    try:
        if "url-to-podcast" in prompt_id:
            result = agent.main("https://en.wikipedia.org/wiki/Alan_Turing_Life")
        else:
            # we are not testing other use-cases atm, but we can expect they will be
            # called with different parameters so we'll have an if...elif...else here
            result = True

        logger.debug(f"Agent execution completed with result: {type(result)}")

    except Exception as e:
        logger.error(f"Exception occurred: {type(e).__name__}: {e}")
        pytest.fail(f"Exception: {type(e).__name__}: {e}")

    assert result is not None
