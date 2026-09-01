"""Application tracking API."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.job import (
    ApplicationDetail,
    ApplicationStatusChange,
    ApplicationStatusHistoryItem,
    ApplicationSummary,
    ApplicationUpdate,
)
from app.services.job_service import JobService

router = APIRouter(prefix="/applications")


def _svc(db: AsyncSession = Depends(get_db)) -> JobService:
    return JobService(db)


@router.get("", response_model=list[ApplicationSummary])
async def list_applications(
    user: User = Depends(get_current_user),
    status: str | None = None,
    service: JobService = Depends(_svc),
) -> list[ApplicationSummary]:
    return await service.list_applications(user, status=status)


@router.get("/{application_id}", response_model=ApplicationDetail)
async def get_application(
    application_id: UUID,
    user: User = Depends(get_current_user),
    service: JobService = Depends(_svc),
) -> ApplicationDetail:
    return await service.get_application(user, application_id)


@router.patch("/{application_id}", response_model=ApplicationDetail)
async def update_application(
    application_id: UUID,
    payload: ApplicationUpdate,
    user: User = Depends(get_current_user),
    service: JobService = Depends(_svc),
) -> ApplicationDetail:
    return await service.update_application(user, application_id, payload)


@router.post("/{application_id}/status", response_model=ApplicationDetail)
async def change_status(
    application_id: UUID,
    payload: ApplicationStatusChange,
    user: User = Depends(get_current_user),
    service: JobService = Depends(_svc),
) -> ApplicationDetail:
    return await service.change_status(user, application_id, payload)


@router.get("/{application_id}/history", response_model=list[ApplicationStatusHistoryItem])
async def application_history(
    application_id: UUID,
    user: User = Depends(get_current_user),
    service: JobService = Depends(_svc),
) -> list[ApplicationStatusHistoryItem]:
    return await service.application_history(user, application_id)
