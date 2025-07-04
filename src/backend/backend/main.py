from collections.abc import Callable
from http import HTTPStatus
from pathlib import Path

from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from backend.api.router import api_router
from backend.api.routes.agents import agent_exception_mappings
from backend.logging import logger
from backend.services.exceptions import ServiceError


def _init_db():
    backend_root = Path(__file__).parent.parent
    alembic_cfg = Config(str(backend_root / "alembic.ini"))
    command.upgrade(alembic_cfg, "head")


def create_error_handler(status_code: HTTPStatus) -> Callable[[Request, ServiceError], Response]:
    """Creates an error handler function for service errors, using the given status code"""

    def handler(_: Request, e: ServiceError) -> Response:
        # Log any inner exceptions as part of handling the service error.
        logger.error(f"Service error: {e.message}")

        return JSONResponse(
            status_code=status_code,
            content={"detail": e.message},
        )

    return handler


def create_app():
    _init_db()

    app = FastAPI()
    app.include_router(api_router)

    exception_mappings = [agent_exception_mappings()]

    # Add a handler for each error -> status mapping.
    for mapping in exception_mappings:
        for key, value in mapping.items():
            app.add_exception_handler(key, create_error_handler(value))

    @app.get("/")
    def get_root():
        return {"Hello": "Agent Factory Backend!🤖"}

    return app


app = create_app()
