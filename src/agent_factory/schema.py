from pydantic import BaseModel, Field


class AgentFactoryOutputs(BaseModel):
    agent_code: str = Field(..., description="The python script as a string that is runnable as agent.py")
    run_instructions: str = Field(..., description="The run instructions in Markdown format")
    dependencies: str = Field(..., description="The dependencies line by line in Markdown format")
