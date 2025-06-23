from fastapi import APIRouter

from backend.api.routes import health

API_V1_PREFIX = "/api/v1"

api_router = APIRouter(prefix=API_V1_PREFIX)
api_router.include_router(health.router, prefix="/health", tags=["health"])
