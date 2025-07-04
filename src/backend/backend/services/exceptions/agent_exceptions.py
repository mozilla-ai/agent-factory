from uuid import UUID

from backend.services.exceptions.base_exceptions import NotFoundError


class AgentNotFoundError(NotFoundError):
    """Raised when a job does not exist."""

    def __init__(self, resource_id: UUID, message: str | None = None, e: Exception | None = None):
        """Creates a JobNotFoundError.

        :param resource_id: UUID of job resource
        :param message: optional error message
        :param e: optional exception, where possible raise ``from e`` to preserve the original traceback
        """
        super().__init__("Agent", str(resource_id), message, e)
