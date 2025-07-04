class ServiceError(Exception):
    """Base exception for service-related errors."""

    def __init__(self, message: str, e: Exception | None = None):
        """Creates a ServiceError.

        :param message: error message
        :param e: optional exception, where possible raise ``from e`` to preserve the original traceback
        """
        super().__init__(message)
        self.message = message
        self.e = e

    def _append_message(self, existing: str, message: str | None) -> str:
        """Appends a ``message`` to the ``existing`` message if it exists.

        :param existing: the existing message.
        :param message: the message to append.
        :return: the combined message joined by ':'.
        """
        return f"{existing}{f': {message}' if message else ''}"


class NotFoundError(ServiceError):
    """Base exception for errors caused by a resource that cannot be found."""

    def __init__(
        self,
        resource: str,
        resource_id: str,
        message: str | None = None,
        e: Exception | None = None,
    ):
        """Creates a NotFoundError.

        :param resource: the resource that was not found
        :param resource_id: the ID of the resource that was not found
        :param message: an optional error message
        :param e: optional exception, where possible raise ``from e`` to preserve the original traceback
        """
        msg = f"{resource} with ID {resource_id} not found."
        super().__init__(self._append_message(msg, message), e)
        self.resource = resource
        self.resource_id = resource_id
