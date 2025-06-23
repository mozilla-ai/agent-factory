from pathlib import Path

from alembic import command
from alembic.config import Config
from fastapi import FastAPI

from backend.api.router import api_router


def _init_db():
    backend_root = Path(__file__).parent.parent
    alembic_cfg = Config(str(backend_root / "alembic.ini"))
    command.upgrade(alembic_cfg, "head")


def create_app():
    _init_db()

    app = FastAPI()
    app.include_router(api_router)

    @app.get("/")
    def get_root():
        return {"Hello": "Agent Factory Backend!🤖"}

    return app


app = create_app()
