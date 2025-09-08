import importlib.metadata

import autoflake

from agent_factory.utils.logging import logger

ANY_AGENT_VERSION = importlib.metadata.version("any_agent")


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


# TODO: pin all dependencies, if known, i.e. if present in the pyproject.toml
def validate_dependencies(tools: str, dependencies: list[str]) -> str:
    """Validate dependencies. In particular:
    - make sure that if uvx is used to install an MCP server, then
      uv appears in the final requirements.txt
    - pin any-agent to the version used by the manufacturing agent
    """
    # make sure uv is in if uvx is in tools
    final_dependencies = []
    final_dependencies.extend(dependencies)

    if "uvx" in tools and "uv" not in final_dependencies:
        logger.info("Agent uses uvx but deps were missing uv: adding manually.")
        final_dependencies.append("uv")

    if "any-agent" in final_dependencies:
        logger.info(f"Pinning any-agent to version {ANY_AGENT_VERSION}")
        final_dependencies = list(filter(lambda dependency: not dependency.startswith("any-agent"), final_dependencies))
        final_dependencies.append(f"any-agent[all,a2a]=={ANY_AGENT_VERSION}")

    return "\n".join(final_dependencies)
