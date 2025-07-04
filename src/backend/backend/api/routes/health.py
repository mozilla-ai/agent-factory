from fastapi import APIRouter

from backend.schemas import HealthResponse

router = APIRouter()


@router.get("/")
def get_health() -> HealthResponse:
    return HealthResponse(status="OK")
