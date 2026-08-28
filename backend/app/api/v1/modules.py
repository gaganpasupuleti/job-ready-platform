from fastapi import APIRouter, Query

from app.schemas.modules import ModulesResponse
from app.services.modules_service import ModulesService

router = APIRouter()
modules_service = ModulesService()


@router.get("/modules", response_model=ModulesResponse)
async def list_modules(
    enabled_only: bool = Query(default=True, description="Return only enabled modules"),
) -> ModulesResponse:
    return modules_service.get_modules(enabled_only=enabled_only)
