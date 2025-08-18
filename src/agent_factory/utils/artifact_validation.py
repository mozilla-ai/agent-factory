import autoflake

from agent_factory.utils.logging import logger

PINNED_ANY_LLM = "any-llm-sdk[openai]==0.13.1"


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
    - Any line starting with `any-llm-sdk` (optionally with extras and any version
      specifiers) is replaced with exactly `any-llm-sdk[openai]==0.13.1`.
    - If no `any-llm-sdk` line exists and dependencies are non-empty, append
      `any-llm-sdk[openai]==0.13.1` as a new line.
    """
    dependencies = agent_factory_outputs["dependencies"]

    # make sure uv is in if uvx is in tools
    if "uvx" in agent_factory_outputs["tools"] and "uv" not in dependencies:
        logger.info("Agent uses uvx but deps were missing uv: adding manually.")
        dependencies += "\nuv"

    # Remove any existing any-llm lines and append pinned constraint
    lines = dependencies.split("\n")
    filtered_lines = [line for line in lines if not line.strip().startswith("any-llm-sdk")]
    filtered_lines.append(PINNED_ANY_LLM)

    normalized_dependencies = "\n".join(filtered_lines)
    agent_factory_outputs["dependencies"] = normalized_dependencies
    return normalized_dependencies
