import datetime as dt
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class HealthResponse(BaseModel):
    status: str


class AgentCreateRequest(BaseModel):
    prompt: str


class AgentSummary(BaseModel):
    id: UUID
    summary: str = Field(title="Summary", description="An AI-generated summary of the purpose of the agent.")
    status: AgentStatus = Field(title="Status", description="The current status of the agent.")
    created_at: dt.datetime = Field(title="Created At", description="The date and time when the agent was created.")


class AgentConfig(AgentSummary):
    prompt: str = Field(title="Prompt", description="The full user prompt used to create the agent.")
    trace_available: bool = Field(
        title="Trace Available", description="True if traces generated during creation are available."
    )
    download_available: bool = Field(
        title="Download Available", description="True if generated agent files are available for downloading."
    )
