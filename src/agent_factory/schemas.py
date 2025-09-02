import ast
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class Status(Enum):
    COMPLETED = "completed"
    INPUT_REQUIRED = "input_required"
    ERROR = "error"


class AgentParameters(BaseModel):
    """Schema for agent_parameters.json file that defines CLI arguments for generated agents."""

    params: dict[str, Literal["string", "integer", "number", "boolean"]] = Field(
        ..., description="Dictionary mapping CLI parameter names (with -- prefix) to their JSON schema types"
    )


class MCPServer(BaseModel):
    name: str = Field(..., description="Name of the MCP server.")
    tools: list[str] = Field(..., description="List of tools to use from the MCP server.")


class AgentFactoryOutputs(BaseModel):
    message: str = Field(..., description="The message to be displayed to the user.")
    status: Status = Field(..., description="The status of the agent's execution.")
    imports: str = Field(..., description="The python code snippet used to import the required tools.")
    agent_instructions: str = Field(..., description="The instructions passed to the generated agent.")
    tools: str = Field(..., description="The python code that defines the tools to be used by the generated agent.")
    mcp_servers: list[MCPServer] | None = Field(
        description="List of MCP servers to be used by the generated agent.", default=None
    )
    structured_outputs: str = Field(..., description="The Pydantic v2 models used to structure the agent's output.")
    cli_args: str = Field(..., description="The arguments to be provided to the agent from the command line.")
    agent_description: str = Field(..., description="The description of the agent and what it does.")
    prompt_template: str = Field(
        ..., description="A prompt template that, completed with cli_args, defines the agent's input prompt."
    )
    readme: str = Field(..., description="The run instructions in Markdown format")


class SyntaxErrorMessage(BaseModel):
    code: str = Field(..., description="The Python code that has the syntax error.")
    message: str = Field(..., description="The error message.")
    line: int | None = Field(..., description="The line number where the error occurred.")
    text: str | None = Field(..., description="The text of the line where the error occurred.")


class CodeSnippet(BaseModel):
    """Validate that the code snippet is syntactically correct Python code.

    This schema accepts a single field 'code' which is a string containing Python code. The code is validated
    using the `ast` module to ensure it is syntactically correct.

    Args:
        code: The Python code snippet as a string.

    Raises:
        SyntaxError: If the code is not valid Python code.
    """

    code: str

    @field_validator("code")
    @classmethod
    def check_valid_python_code(cls, value: str) -> str:
        """Validate that the input string is syntactically correct Python code.

        Use the `ast` module to parse the code.
        If the code syntax is incorrect, a `SyntaxError` will be raised.

        Args:
            value: The string value of the 'code' field.

        Returns:
            The original string if it's valid Python code.

        Raises:
            ValueError: If the code has a syntax error.
        """
        try:
            ast.parse(value)
        except SyntaxError:
            raise

        return value
