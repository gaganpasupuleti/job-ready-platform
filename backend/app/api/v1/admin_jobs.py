"""Admin jobs and import API."""

from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_admin
from app.core.exceptions import AppException
from app.db.session import get_db
from app.models.user import User
from app.schemas.job import (
    AdminJobCreate,
    AdminJobUpdate,
    ImportConfirmRequest,
    ImportConfirmResponse,
    ImportPreviewResponse,
    IngestionErrorPublic,
    IngestionRunPublic,
    JobCard,
    JobSourcePublic,
    PublicationDecisionPublic,
    PublicationDecisionWrite,
)
from app.services.jobs_source_sync import list_publication_decisions, record_publication_decision
from app.services.admin_job_service import AdminJobService

router = APIRouter(prefix="/admin/jobs")

MAX_UPLOAD_BYTES = 10 * 1024 * 1024


def _svc(db: AsyncSession = Depends(get_db)) -> AdminJobService:
    return AdminJobService(db)


@router.get("", response_model=dict)
async def admin_list_jobs(
    _admin: User = Depends(get_current_admin),
    status: str | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=100),
    service: AdminJobService = Depends(_svc),
) -> dict:
    return await service.list_jobs(status=status, page=page, limit=limit)


@router.post("", response_model=JobCard)
async def admin_create_job(
    payload: AdminJobCreate,
    _admin: User = Depends(get_current_admin),
    service: AdminJobService = Depends(_svc),
) -> JobCard:
    return await service.create_job(payload)


@router.patch("/{job_id}", response_model=JobCard)
async def admin_update_job(
    job_id: UUID,
    payload: AdminJobUpdate,
    _admin: User = Depends(get_current_admin),
    service: AdminJobService = Depends(_svc),
) -> JobCard:
    return await service.update_job(job_id, payload)


@router.post("/{job_id}/archive", status_code=204)
async def admin_archive_job(
    job_id: UUID,
    _admin: User = Depends(get_current_admin),
    service: AdminJobService = Depends(_svc),
) -> None:
    await service.archive_job(job_id)


@router.get("/sources", response_model=list[JobSourcePublic])
async def admin_sources(
    _admin: User = Depends(get_current_admin),
    service: AdminJobService = Depends(_svc),
) -> list[JobSourcePublic]:
    return await service.list_sources()


@router.get("/imports", response_model=list[IngestionRunPublic])
async def admin_import_runs(
    _admin: User = Depends(get_current_admin),
    service: AdminJobService = Depends(_svc),
) -> list[IngestionRunPublic]:
    return await service.list_import_runs()


@router.get("/imports/{run_id}/errors", response_model=list[IngestionErrorPublic])
async def admin_import_errors(
    run_id: UUID,
    _admin: User = Depends(get_current_admin),
    service: AdminJobService = Depends(_svc),
) -> list[IngestionErrorPublic]:
    return await service.import_errors(run_id)


@router.post("/imports/validate", response_model=ImportPreviewResponse)
async def admin_validate_import(
    file: UploadFile = File(...),
    _admin: User = Depends(get_current_admin),
    service: AdminJobService = Depends(_svc),
) -> ImportPreviewResponse:
    raw = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(raw) > MAX_UPLOAD_BYTES:
        raise AppException("File exceeds 10 MB limit", status_code=400)
    content = raw.decode("utf-8-sig", errors="replace")
    return await service.validate_csv(content, file.filename or "upload.csv")


@router.get("/publication-decisions", response_model=list[PublicationDecisionPublic])
async def admin_list_publication_decisions(
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> list[PublicationDecisionPublic]:
    rows = await list_publication_decisions(db)
    return [
        PublicationDecisionPublic(source=row.source, source_job_id=row.source_job_id, decision=row.decision)
        for row in rows
    ]


@router.post("/publication-decisions", response_model=PublicationDecisionPublic)
async def admin_record_publication_decision(
    payload: PublicationDecisionWrite,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> PublicationDecisionPublic:
    source = payload.source.strip().lower()
    job_id = payload.source_job_id.strip()
    if not source or not job_id or any(ch.isspace() for ch in source) or any(ch.isspace() for ch in job_id):
        raise AppException("Source and job id cannot contain spaces.", status_code=400)
    try:
        await record_publication_decision(db, source=source, job_id=job_id, decision=payload.decision)
    except ValueError as exc:
        raise AppException(str(exc), status_code=400) from exc
    return PublicationDecisionPublic(source=source, source_job_id=job_id, decision=payload.decision)


@router.post("/imports/confirm", response_model=ImportConfirmResponse)
async def admin_confirm_import(
    payload: ImportConfirmRequest,
    _admin: User = Depends(get_current_admin),
    service: AdminJobService = Depends(_svc),
) -> ImportConfirmResponse:
    return await service.confirm_import(payload.preview_id, payload.filename)
