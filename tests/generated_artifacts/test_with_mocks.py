import importlib
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from mock_tools import find_matching_mock

from agent_factory.utils.logging import logger

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

    def tool_type_checker(tool, type_name):
        """Check if a tool matches a given type"""
        if type_name == "MCPStdio":
            return isinstance(tool, MCPStdio)
        elif type_name == "function":
            # as we match the mock to (a substring of) the function name,
            # we expect the function to have one
            return callable(tool) and hasattr(tool, "__name__")
        return False

    async def mocking_load_tools(self, tools):
        logger.info(f"AnyAgent._load_tools called with {len(tools)} tools:")
        for i, tool in enumerate(tools):
            logger.info(f"    Tool {i}: {type(tool)} - {tool}")

        # Process tools and replace with mocks where applicable
        modified_tools = []
        for tool in tools:
            # Try to find a matching mock
            mock_function = find_matching_mock(tool, tool_type_checker)

            if mock_function:
                logger.info(f"Replacing tool {tool} with mock {mock_function.__name__}")
                modified_tools.append(mock_function)
            else:
                # No mock found, keep original tool
                modified_tools.append(tool)

        logger.info(f"Modified tools count: {len(modified_tools)}")
        for i, tool in enumerate(modified_tools):
            logger.info(f"  Tool {i}: {type(tool)} - {tool}")

        # Call original method with modified tools
        result = await original_load_tools(self, modified_tools)

        logger.info(f"Original _load_tools returned: {len(result[0])} tools, {len(result[1])} mcp_servers")

        return result

    try:
        # Patch _load_tools before importing agent
        with patch.object(AnyAgent, "_load_tools", mocking_load_tools):
            logger.info("Patched AnyAgent._load_tools")

            # Import the agent module
            if "agent" in sys.modules:
                importlib.reload(sys.modules["agent"])
            else:
                import agent

            logger.info("Agent module imported successfully")

            yield agent

    finally:
        # Clean up
        sys.path.remove(str(agent_dir))
        if "agent" in sys.modules:
            del sys.modules["agent"]


def test_agent_mocked_execution(generated_agent_module_with_mocks):
    """Test agent execution with _load_tools mocking"""
    agent = generated_agent_module_with_mocks

    logger.info("Starting agent execution...")

    try:
        result = agent.main("https://aittalam.github.io/posts/2023-12-31-setting-up-hugo/")
        logger.info(f"Agent execution completed with result: {type(result)}")

    except Exception as e:
        logger.error(f"Exception occurred: {type(e).__name__}: {e}")
        pytest.fail(f"Exception: {type(e).__name__}: {e}")

    assert result is not None
