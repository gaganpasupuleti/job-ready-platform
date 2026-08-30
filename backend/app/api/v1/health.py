from fastapi import APIRouter

from app.schemas.health import DetailedHealthResponse
from app.services.health_service import HealthService

router = APIRouter()
health_service = HealthService()


@router.get("/health", response_model=DetailedHealthResponse)
async def health_check() -> DetailedHealthResponse:
    return await health_service.get_health_detailed()
