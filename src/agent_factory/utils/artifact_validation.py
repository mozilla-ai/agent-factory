import autoflake

from agent_factory.utils.logging import logger


def clean_python_code_with_autoflake(code: str) -> str:
    """Clean Python code using autoflake to remove unused imports (F401) and variables (F841)."""
    try:
        cleaned_code = autoflake.fix_code(
            code,
            remove_all_unused_imports=True,
            remove_unused_variables=True,
        )
        return cleaned_code
    except Exception as e:
        logger.error(f"Error while running autoflake to clean Python code: {e}")
        raise


def validate_dependencies(agent_factory_outputs: dict[str, str]) -> str:
    """Validate dependencies. In particular:
    - make sure that if uvx is used to install an MCP server, then
      uv appears in the final requirements.txt
    """
    # make sure uv is in if uvx is in tools
    if "uvx" in agent_factory_outputs["tools"] and "uv" not in agent_factory_outputs["dependencies"]:
        logger.info("Agent uses uvx but deps were missing uv: adding manually.")
        agent_factory_outputs["dependencies"] += "\nuv"

    return agent_factory_outputs["dependencies"]
