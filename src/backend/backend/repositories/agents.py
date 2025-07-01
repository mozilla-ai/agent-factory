from sqlalchemy.orm import Session

from backend.records.agents import AgentRecord
from backend.repositories.base import BaseRepository


class AgentRepository(BaseRepository[AgentRecord]):
    def __init__(self, session: Session):
        super().__init__(AgentRecord, session)
