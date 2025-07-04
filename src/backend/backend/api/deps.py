from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from backend.db import session_manager
from backend.repositories.agents import AgentRepository
from backend.services.agents import AgentService


def get_db_session() -> Generator[Session, None, None]:
    with session_manager.session() as session:
        yield session


DBSessionDep = Annotated[Session, Depends(get_db_session)]


def get_agent_service(session: DBSessionDep) -> AgentService:
    agent_repository = AgentRepository(session)
    return AgentService(agent_repository)


AgentServiceDep = Annotated[AgentService, Depends(get_agent_service)]
