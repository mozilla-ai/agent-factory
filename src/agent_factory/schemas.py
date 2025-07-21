from pydantic import BaseModel, Field


class AgentFactoryOutputs(BaseModel):
    agent_instructions: str = Field(..., description="The instructions passed to the generated agent.")
    tools: str = Field(..., description="The python code that defines the tools to be used by the generated agent.")
    imports: str = Field(..., description="The python code snippet used to import the required tools.")
    structured_outputs: str = Field(..., description="The Pydantic v2 models used to structure the agent's output.")
    cli_args: str = Field(..., description="The arguments to be provided to the agent from the command line.")
    agent_description: str = Field(..., description="The description of the agent and what it does.")
    prompt_template: str = Field(
        ..., description="A prompt template that, completed with cli_args, defines the agent's input prompt."
    )
    readme: str = Field(..., description="The run instructions in Markdown format")
    dependencies: str = Field(..., description="The dependencies line by line in Markdown format")
