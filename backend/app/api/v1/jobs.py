"""Student jobs API."""

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
    JobDetail,
    JobListResponse,
    JobPreferenceUpdate,
    JobsSummary,
    SavedJobItem,
)
from app.services.job_service import JobService

router = APIRouter(prefix="/jobs")


def _svc(db: AsyncSession = Depends(get_db)) -> JobService:
    return JobService(db)


@router.get("", response_model=JobListResponse)
async def list_jobs(
    user: User = Depends(get_current_user),
    q: str | None = None,
    role: str | None = None,
    skill: str | None = None,
    company: str | None = None,
    city: str | None = None,
    state: str | None = None,
    country: str | None = None,
    remote: bool | None = None,
    work_mode: str | None = None,
    employment_type: str | None = None,
    experience_min: int | None = None,
    posted_within_days: int | None = None,
    sort: str = Query(default="newest"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=50),
    service: JobService = Depends(_svc),
) -> JobListResponse:
    return await service.list_jobs(
        user,
        q=q,
        role=role,
        skill=skill,
        company=company,
        city=city,
        state=state,
        country=country,
        remote=remote,
        work_mode=work_mode,
        employment_type=employment_type,
        experience_min=experience_min,
        posted_within_days=posted_within_days,
        sort=sort,
        page=page,
        limit=limit,
    )


@router.get("/summary", response_model=JobsSummary)
async def jobs_summary(
    user: User = Depends(get_current_user),
    service: JobService = Depends(_svc),
) -> JobsSummary:
    return await service.summary(user)


@router.get("/saved", response_model=list[SavedJobItem])
async def saved_jobs(
    user: User = Depends(get_current_user),
    service: JobService = Depends(_svc),
) -> list[SavedJobItem]:
    return await service.list_saved(user)


@router.get("/recommended", response_model=JobListResponse)
async def recommended_jobs(
    user: User = Depends(get_current_user),
    limit: int = Query(default=20, ge=1, le=50),
    sort: str = Query(default="coverage"),
    service: JobService = Depends(_svc),
) -> JobListResponse:
    return await service.recommended(user, limit=limit, sort=sort)


@router.get("/{job_id}/match")
async def job_match(
    job_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.job_match_service import JobMatchService

    return await JobMatchService(db).match_job(user, job_id)


@router.get("/{job_id}", response_model=JobDetail)
async def job_detail(
    job_id: str,
    user: User = Depends(get_current_user),
    service: JobService = Depends(_svc),
) -> JobDetail:
    return await service.get_job(user, job_id)


@router.post("/{job_id}/save", status_code=204)
async def save_job(
    job_id: UUID,
    user: User = Depends(get_current_user),
    service: JobService = Depends(_svc),
) -> None:
    await service.save_job(user, job_id)


@router.delete("/{job_id}/save", status_code=204)
async def unsave_job(
    job_id: UUID,
    user: User = Depends(get_current_user),
    service: JobService = Depends(_svc),
) -> None:
    await service.unsave_job(user, job_id)


@router.post("/{job_id}/apply", response_model=ApplicationDetail)
async def mark_applied(
    job_id: UUID,
    user: User = Depends(get_current_user),
    service: JobService = Depends(_svc),
) -> ApplicationDetail:
    return await service.mark_applied(user, job_id)


@router.post("/{job_id}/prepare", response_model=ApplicationDetail)
async def start_preparing(
    job_id: UUID,
    user: User = Depends(get_current_user),
    service: JobService = Depends(_svc),
) -> ApplicationDetail:
    return await service.create_application_preparing(user, job_id)


@router.put("/preferences", status_code=204)
async def update_preferences(
    payload: JobPreferenceUpdate,
    user: User = Depends(get_current_user),
    service: JobService = Depends(_svc),
) -> None:
    await service.update_preference(user, payload)
