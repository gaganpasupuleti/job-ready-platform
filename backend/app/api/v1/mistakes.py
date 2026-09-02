"""Mistake book API."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.mistake import MistakeItemResponse, MistakeSummary, RetrySessionRequest
from app.schemas.practice import SessionDetailResponse
from app.services.mistake_service import MistakeService
from app.services.practice_service import PracticeService

router = APIRouter(prefix="/mistakes")


def _svc(db: AsyncSession = Depends(get_db)) -> MistakeService:
    return MistakeService(db)


@router.get("", response_model=list[MistakeItemResponse])
async def list_mistakes(
    user: User = Depends(get_current_user),
    source_type: str | None = None,
    status: str | None = None,
    view: str = Query(default="recent"),
    service: MistakeService = Depends(_svc),
) -> list[MistakeItemResponse]:
    items = await service.list_mistakes(user, source_type=source_type, status=status, view=view)
    return [MistakeItemResponse(**i) for i in items]


@router.get("/summary", response_model=MistakeSummary)
async def mistake_summary(
    user: User = Depends(get_current_user),
    service: MistakeService = Depends(_svc),
) -> MistakeSummary:
    return MistakeSummary(**await service.summary(user))


@router.post("/{mistake_id}/review", response_model=MistakeItemResponse)
async def mark_reviewed(
    mistake_id: UUID,
    user: User = Depends(get_current_user),
    service: MistakeService = Depends(_svc),
) -> MistakeItemResponse:
    return MistakeItemResponse(**await service.mark_reviewed(user, mistake_id))


@router.patch("/{mistake_id}", response_model=MistakeItemResponse)
async def resolve_mistake(
    mistake_id: UUID,
    user: User = Depends(get_current_user),
    service: MistakeService = Depends(_svc),
) -> MistakeItemResponse:
    return MistakeItemResponse(**await service.resolve(user, mistake_id))


@router.post("/retry-session", response_model=SessionDetailResponse)
async def retry_mcq_session(
    payload: RetrySessionRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SessionDetailResponse:
    practice = PracticeService(db)
    return await practice.create_retry_session(user, [UUID(q) for q in payload.question_ids])
