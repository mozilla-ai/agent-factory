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


# TODO: pin all dependencies, if known, i.e. if present in the pyproject.toml
def validate_dependencies(agent_factory_outputs: dict[str, str]) -> str:
    """Validate dependencies. In particular:
    - make sure that if uvx is used to install an MCP server, then
      uv appears in the final requirements.txt
    - Any line starting with `litellm` (optionally with extras and any version
      specifiers) is replaced with exactly `litellm<1.75.0`.
    - If no `litellm` line exists and dependencies are non-empty, append
      `litellm<1.75.0` as a new line.
    - if visit_webpage is in tools, add markdownify==1.2.0 to dependencies
    - if search_tavily is in tools, add tavily-python==0.7.10 to dependencies
    """
    dependencies = agent_factory_outputs["dependencies"]

    # make sure uv is in if uvx is in tools
    if "uvx" in agent_factory_outputs["tools"] and "uv" not in dependencies:
        logger.info("Agent uses uvx but deps were missing uv: adding manually.")
        dependencies += "\nuv"

    # We know markdownify is a dependency of visit_webpage
    # TODO: parse tool deps and add them to the dependencies, rather than manually here
    if "visit_webpage" in agent_factory_outputs["tools"] and "markdownify" not in dependencies:
        logger.info("Agent uses visit_webpage but deps were missing markdownify: adding manually.")
        dependencies += "\nmarkdownify==1.2.0"

    # TODO: same as a above
    if "search_tavily" in agent_factory_outputs["tools"] and "tavily-python" not in dependencies:
        logger.info("Agent uses search_tavily but deps were missing tavily-python: adding manually.")
        dependencies += "\ntavily-python==0.7.10"

    # Remove any existing litellm lines and append pinned constraint
    lines = dependencies.split("\n")
    filtered_lines = [line for line in lines if not line.strip().startswith("litellm")]
    filtered_lines.append("litellm<1.75.0")

    normalized_dependencies = "\n".join(filtered_lines)
    agent_factory_outputs["dependencies"] = normalized_dependencies
    return normalized_dependencies
