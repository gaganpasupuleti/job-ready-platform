from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.content.reports import daily_report, gap_report
from app.core.deps import get_current_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.interview import (
    BulkIds,
    ContentBatchAdmin,
    ContentBatchListResponse,
    ContentCandidateAdmin,
    ContentCandidateListResponse,
    ContentCandidateUpdate,
)
from app.services.interview_content_service import InterviewContentService

router = APIRouter(prefix="/admin/content")


@router.get("/batches", response_model=ContentBatchListResponse)
async def list_batches(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> ContentBatchListResponse:
    return await InterviewContentService(db).list_batches(skip=skip, limit=limit)


@router.get("/batches/{batch_id}", response_model=ContentBatchAdmin)
async def get_batch(
    batch_id: UUID,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> ContentBatchAdmin:
    return await InterviewContentService(db).get_batch(batch_id)


@router.get("/candidates", response_model=ContentCandidateListResponse)
async def list_candidates(
    batch_id: UUID | None = None,
    review_status: str | None = None,
    skill: str | None = None,
    role: str | None = None,
    company: str | None = None,
    difficulty: str | None = None,
    content_type: str | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> ContentCandidateListResponse:
    return await InterviewContentService(db).list_candidates(
        batch_id=batch_id,
        review_status=review_status,
        skill=skill,
        role=role,
        company=company,
        difficulty=difficulty,
        content_type=content_type,
        skip=skip,
        limit=limit,
    )


@router.patch("/candidates/{candidate_id}", response_model=ContentCandidateAdmin)
async def edit_candidate(
    candidate_id: UUID,
    payload: ContentCandidateUpdate,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> ContentCandidateAdmin:
    return await InterviewContentService(db).update_candidate(candidate_id, payload)


@router.post("/candidates/{candidate_id}/approve", response_model=ContentCandidateAdmin)
async def approve_candidate(
    candidate_id: UUID,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> ContentCandidateAdmin:
    return await InterviewContentService(db).approve_candidate(candidate_id, admin.id)


@router.post("/candidates/{candidate_id}/reject", response_model=ContentCandidateAdmin)
async def reject_candidate(
    candidate_id: UUID,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> ContentCandidateAdmin:
    return await InterviewContentService(db).reject_candidate(candidate_id)


@router.post("/candidates/bulk-approve")
async def bulk_approve(
    payload: BulkIds,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await InterviewContentService(db).bulk_approve(payload.ids, admin.id)


@router.get("/gaps")
async def content_gaps(
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await gap_report(db)


@router.get("/daily-report")
async def content_daily_report(
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await daily_report(db)
