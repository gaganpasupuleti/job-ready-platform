from fastapi import APIRouter

from app.schemas.health import HealthResponse
from app.services.health_service import HealthService

router = APIRouter()
health_service = HealthService()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return health_service.get_health()
