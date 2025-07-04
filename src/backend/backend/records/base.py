from typing import Any

from sqlalchemy import JSON
from sqlalchemy.orm import DeclarativeBase

from backend.records.mixins import PrimaryKeyMixin


class BaseRecord(DeclarativeBase, PrimaryKeyMixin):
    """Base class for declarative SQLAlchemy mappings."""

    type_annotation_map = {dict[str, Any]: JSON}
