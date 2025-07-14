from uuid import UUID

from fastapi import APIRouter, status
from fastapi.responses import FileResponse
from starlette.requests import Request
from starlette.responses import Response

from backend.api.deps import AgentServiceDep
from backend.schemas import AgentConfig, AgentCreateRequest, AgentSummary
from backend.services.exceptions import AgentNotFoundError

router = APIRouter()


def agent_exception_mappings() -> dict[type[AgentNotFoundError], int]:
    return {
        AgentNotFoundError: status.HTTP_404_NOT_FOUND,
    }


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_agent(
    service: AgentServiceDep,
    agent_create_request: AgentCreateRequest,
    request: Request,
    response: Response,
) -> AgentSummary:
    agent_summary = await service.create_agent(agent_create_request)
    url = request.url_for(get_agent.__name__, agent_id=agent_summary.id)
    response.headers["Location"] = f"{url}"
    return agent_summary


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
    return service.list_agents()


@router.get("/{agent_id}/download")
def download_agent(
    service: AgentServiceDep,
    agent_id: UUID,
) -> FileResponse:
    file_path = service.download_agent(agent_id)
    return FileResponse(path=file_path, filename=f"{agent_id}.zip", media_type="application/octet-stream")
