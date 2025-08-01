from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class Status(Enum):
    COMPLETED = "completed"
    INPUT_REQUIRED = "input_required"
    ERROR = "error"


class AgentParameters(BaseModel):
    """Schema for agent_parameters.json file that defines CLI arguments for generated agents."""

    params: dict[str, Literal["string", "integer", "number", "boolean"]] = Field(
        ..., description="Dictionary mapping CLI parameter names (with -- prefix) to their JSON schema types"
    )


class AgentFactoryOutputs(BaseModel):
    message: str = Field(..., description="The message to be displayed to the user.")
    status: Status = Field(..., description="The status of the agent's execution.")
    imports: str = Field(..., description="The python code snippet used to import the required tools.")
    agent_instructions: str = Field(..., description="The instructions passed to the generated agent.")
    tools: str = Field(..., description="The python code that defines the tools to be used by the generated agent.")
    structured_outputs: str = Field(..., description="The Pydantic v2 models used to structure the agent's output.")
    cli_args: str = Field(..., description="The arguments to be provided to the agent from the command line.")
    agent_description: str = Field(..., description="The description of the agent and what it does.")
    prompt_template: str = Field(
        ..., description="A prompt template that, completed with cli_args, defines the agent's input prompt."
    )
    readme: str = Field(..., description="The run instructions in Markdown format")
    dependencies: str = Field(..., description="The dependencies line by line in Markdown format")
