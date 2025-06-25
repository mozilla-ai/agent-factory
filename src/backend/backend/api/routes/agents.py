from uuid import UUID

from fastapi import APIRouter, status
from fastapi.responses import FileResponse

from backend.api.deps import AgentServiceDep
from backend.schemas import AgentConfig, AgentCreateRequest, AgentSummary

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_agent(
    service: AgentServiceDep,
    agent_create_request: AgentCreateRequest,
) -> AgentSummary:
    return await service.create_agent(agent_create_request)


@router.get("/{agent_id}", response_model=AgentConfig)
def get_agent(
    service: AgentServiceDep,
    agent_id: UUID,
) -> AgentConfig:
    return service.get_agent(agent_id)


@router.get("/", response_model=list[AgentSummary])
def get_agents(
    service: AgentServiceDep,
) -> list[AgentSummary]:
    return service.get_agents()


@router.get("/{agent_id}/download")
def download_agent(
    service: AgentServiceDep,
    agent_id: UUID,
) -> FileResponse:
    file_path = service.download_agent(agent_id)
    try:
        return FileResponse(path=file_path, filename=f"{agent_id}.zip", media_type="application/octet-stream")
    except Exception as e:
        raise FileNotFoundError(f"File not found for agent {agent_id}: {e}") from e
