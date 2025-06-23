from fastapi import FastAPI

from backend.api.router import api_router


def create_app():
    app = FastAPI()
    app.include_router(api_router)

    @app.get("/")
    def get_root():
        return {"Hello": "Agent Factory Backend!🤖"}

    return app


app = create_app()
