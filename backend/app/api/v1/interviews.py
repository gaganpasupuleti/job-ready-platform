"""Interview session + hub APIs under /api/v1/interviews (content stays on /interview)."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.interview_session import (
    CompanyPrepCard,
    CompanyPrepDetail,
    InterviewHubResponse,
    InterviewNeedsReviewItem,
    InterviewNotesPayload,
    InterviewProgressResponse,
    InterviewReviewPayload,
    InterviewSessionCreate,
    InterviewSessionDetail,
    InterviewSessionQuestionPublic,
    InterviewSessionResults,
    InterviewSessionSummary,
    InterviewPackDetail,
)
from app.services.company_prep_service import CompanyPrepService
from app.services.interview_session_service import InterviewSessionService

router = APIRouter(prefix="/interviews")


def _svc(db: AsyncSession = Depends(get_db)) -> InterviewSessionService:
    return InterviewSessionService(db)


@router.get("/hub", response_model=InterviewHubResponse)
async def interview_hub(
    user: User = Depends(get_current_user),
    service: InterviewSessionService = Depends(_svc),
) -> InterviewHubResponse:
    return await service.hub(user)


@router.get("/packs/{slug}", response_model=InterviewPackDetail)
async def pack_detail(
    slug: str,
    user: User = Depends(get_current_user),
    service: InterviewSessionService = Depends(_svc),
) -> InterviewPackDetail:
    return await service.pack_detail(user, slug)


@router.post("/sessions", response_model=InterviewSessionDetail)
async def create_session(
    payload: InterviewSessionCreate,
    user: User = Depends(get_current_user),
    service: InterviewSessionService = Depends(_svc),
) -> InterviewSessionDetail:
    return await service.create_session(user, payload)


@router.get("/sessions/{session_id}", response_model=InterviewSessionDetail)
async def get_session(
    session_id: UUID,
    user: User = Depends(get_current_user),
    service: InterviewSessionService = Depends(_svc),
) -> InterviewSessionDetail:
    return await service.get_session(user, session_id)


@router.get(
    "/sessions/{session_id}/questions/{number}",
    response_model=InterviewSessionQuestionPublic,
)
async def get_session_question(
    session_id: UUID,
    number: int,
    user: User = Depends(get_current_user),
    service: InterviewSessionService = Depends(_svc),
) -> InterviewSessionQuestionPublic:
    return await service.get_question(user, session_id, number)


@router.post(
    "/sessions/{session_id}/questions/{number}/notes",
    response_model=InterviewSessionQuestionPublic,
)
async def save_notes(
    session_id: UUID,
    number: int,
    payload: InterviewNotesPayload,
    user: User = Depends(get_current_user),
    service: InterviewSessionService = Depends(_svc),
) -> InterviewSessionQuestionPublic:
    return await service.save_notes(user, session_id, number, payload)


@router.post(
    "/sessions/{session_id}/questions/{number}/reveal",
    response_model=InterviewSessionQuestionPublic,
)
async def reveal_answer(
    session_id: UUID,
    number: int,
    user: User = Depends(get_current_user),
    service: InterviewSessionService = Depends(_svc),
) -> InterviewSessionQuestionPublic:
    return await service.reveal(user, session_id, number)


@router.post(
    "/sessions/{session_id}/questions/{number}/review",
    response_model=InterviewSessionQuestionPublic,
)
async def submit_review(
    session_id: UUID,
    number: int,
    payload: InterviewReviewPayload,
    user: User = Depends(get_current_user),
    service: InterviewSessionService = Depends(_svc),
) -> InterviewSessionQuestionPublic:
    return await service.submit_review(user, session_id, number, payload)


@router.post("/sessions/{session_id}/complete", response_model=InterviewSessionResults)
async def complete_session(
    session_id: UUID,
    user: User = Depends(get_current_user),
    service: InterviewSessionService = Depends(_svc),
) -> InterviewSessionResults:
    return await service.complete(user, session_id)


@router.post("/sessions/{session_id}/abandon", response_model=InterviewSessionSummary)
async def abandon_session(
    session_id: UUID,
    user: User = Depends(get_current_user),
    service: InterviewSessionService = Depends(_svc),
) -> InterviewSessionSummary:
    return await service.abandon(user, session_id)


@router.get("/sessions/{session_id}/results", response_model=InterviewSessionResults)
async def session_results(
    session_id: UUID,
    user: User = Depends(get_current_user),
    service: InterviewSessionService = Depends(_svc),
) -> InterviewSessionResults:
    return await service.results(user, session_id)


@router.get("/history", response_model=list[InterviewSessionSummary])
async def interview_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user: User = Depends(get_current_user),
    service: InterviewSessionService = Depends(_svc),
) -> list[InterviewSessionSummary]:
    return await service.history(user, skip=skip, limit=limit)


@router.get("/progress", response_model=InterviewProgressResponse)
async def interview_progress(
    user: User = Depends(get_current_user),
    service: InterviewSessionService = Depends(_svc),
) -> InterviewProgressResponse:
    return await service.progress(user)


@router.get("/review", response_model=list[InterviewNeedsReviewItem])
async def needs_review_queue(
    user: User = Depends(get_current_user),
    service: InterviewSessionService = Depends(_svc),
) -> list[InterviewNeedsReviewItem]:
    return await service.needs_review(user)


@router.post("/review/{question_id}/mark-reviewed", response_model=InterviewNeedsReviewItem)
async def mark_question_reviewed(
    question_id: UUID,
    user: User = Depends(get_current_user),
    service: InterviewSessionService = Depends(_svc),
) -> InterviewNeedsReviewItem:
    return await service.mark_reviewed(user, question_id)


@router.get("/company-prep", response_model=list[CompanyPrepCard])
async def company_prep_list(
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[CompanyPrepCard]:
    return await CompanyPrepService(db).list_companies()


@router.get("/company-prep/{slug}", response_model=CompanyPrepDetail)
async def company_prep_detail(
    slug: str,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CompanyPrepDetail:
    return await CompanyPrepService(db).detail(slug)
