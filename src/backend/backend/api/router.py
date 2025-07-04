from fastapi import APIRouter

from backend.api.routes import agents, health
from backend.api.tags import Tags

API_V1_PREFIX = "/api/v1"

api_router = APIRouter(prefix=API_V1_PREFIX)
api_router.include_router(health.router, prefix="/health", tags=[Tags.HEALTH])
api_router.include_router(agents.router, prefix="/agents", tags=[Tags.AGENTS])
