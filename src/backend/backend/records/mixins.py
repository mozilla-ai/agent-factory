import datetime
import uuid

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, declarative_mixin, mapped_column

from backend.schemas import AgentStatus


@declarative_mixin
class PrimaryKeyMixin:
    # All records have an 'id' primary key
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)


@declarative_mixin
class CreatedAtMixin:
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


@declarative_mixin
class UpdatedAtMixin:
    updated_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True,
    )


@declarative_mixin
class DateTimeMixin(CreatedAtMixin, UpdatedAtMixin):
    pass


@declarative_mixin
class AgentStatusMixin:
    status: Mapped[AgentStatus] = mapped_column(default=AgentStatus.PENDING)
