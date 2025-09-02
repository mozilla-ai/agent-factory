import importlib.metadata
import json

import autoflake
from any_llm import completion

from agent_factory.schemas import CodeSnippet, SyntaxErrorMessage
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


def fix_python_syntax_errors(error_message: SyntaxErrorMessage, model: str = "gpt-4o-mini") -> str:
    """Fix Python syntax issues in the code.

    Use an LLM to suggest a fix for the provided Python code that has a syntax error. The LLM is prompted
    with the code snippet and the error message, and it is expected to return a corrected version of the code.

    Args:
        error_message: An instance of SyntaxErrorMessage containing the code with the details of the syntax error.
        model: The LLM model to use for generating the fix.
        provider: The LLM provider to use.

    Returns:
        A string containing the fixed Python code.
    """
    content = f"""
    Fix the error in the following Python code:

    ```python
    {error_message.code}
    ```

    The error message is: {error_message.message} on line {error_message.line}: {error_message.text}

    You should return the whole code snippet again, fixed.
    """
    response = completion(
        model=model,
        messages=[{"content": content, "role": "user"}],
        response_format=CodeSnippet,  # Code validation does not run at this point
    )

    try:
        python_code = json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        logger.error(f"Failed to decode JSON response: {response.choices[0].message.content}")
        raise

    return python_code.get("code", error_message.code)


def validate_python_syntax(
    code: str,
    max_retries: int = 3,
    attempt: int = 1,
    model: str = "gpt-4o-mini",
) -> CodeSnippet:
    """Validate Python code syntax recursively.

    If a syntax error is found, the function attempts to fix it using an LLM up to a specified number of retries to
    avoid infinite recursion.

    Args:
        code: The Python code string to validate.
        max_retries: The maximum number of times to attempt a fix.
        attempt: The current attempt number (used for recursion).

    Returns:
        A CodeSnippet instance containing the valid Python code.

    Raises:
        SyntaxError: If the code cannot be fixed after the maximum number of retries.
    """
    try:
        return CodeSnippet(code=code)  # This will internally validate the syntax and raise if invalid
    except SyntaxError as e:
        logger.error(f"Found a syntax error. Trying to fix it... (Attempt {attempt}/{max_retries})")

        if attempt > max_retries:
            logger.error(f"Failed to fix the syntax error after {max_retries} attempts.")
            raise

        error_message = SyntaxErrorMessage(
            code=code,
            message=e.msg,
            line=e.lineno,
            text=e.text.strip() if e.text else None,
        )
        logger.error(f"Error details: {e.msg} on line {e.lineno}")

        try:
            fixed_code = fix_python_syntax_errors(error_message, model=model)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON response while fixing syntax errors: {e}")
            raise

        logger.debug(
            "A syntax error was caught during Agent code generation. "
            "An fix was suggested. Re-validating the new code..."
        )
        return validate_python_syntax(fixed_code, max_retries, attempt + 1, model=model)


def prepare_python_code(code: str) -> CodeSnippet:
    try:
        cleaned_code = clean_python_code_with_autoflake(code)
        return validate_python_syntax(cleaned_code, max_retries=3, attempt=1, model="gpt-4o-mini")
    except SyntaxError as e:
        logger.error(f"Agent's code contains syntax errors: {e}")
        raise e
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON response from the LLM while preparing Python code: {e}")
        raise
    except Exception as e:
        logger.error(f"Error while preparing Python code: {e}")
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
        final_dependencies.append(f"any-agent[all]=={ANY_AGENT_VERSION}")

    return "\n".join(final_dependencies)
