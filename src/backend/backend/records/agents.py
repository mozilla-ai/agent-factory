from sqlalchemy.orm import Mapped

from backend.records.base import BaseRecord
from backend.records.mixins import AgentStatusMixin, DateTimeMixin


class AgentRecord(BaseRecord, DateTimeMixin, AgentStatusMixin):
    __tablename__ = "agents"

    summary: Mapped[str]
    prompt: Mapped[str]
    trace_available: Mapped[bool]
    download_available: Mapped[bool]
