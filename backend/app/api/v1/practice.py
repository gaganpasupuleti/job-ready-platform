from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.mistake import RetrySessionRequest
from app.schemas.practice import (
    AnswerRequest,
    AnswerResponse,
    AutosaveRequest,
    CatalogResponse,
    CreateSessionRequest,
    HistoryResponse,
    SessionDetailResponse,
    SessionNavigatorResponse,
    SessionQuestionResponse,
    SessionResultsResponse,
)
from app.services.catalog_service import CatalogService
from app.services.practice_service import PracticeService

router = APIRouter(prefix="/practice")


@router.get("/catalog", response_model=CatalogResponse)
async def get_catalog(
    _current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CatalogResponse:
    return await CatalogService(db).get_catalog()


@router.post("/sessions", response_model=SessionDetailResponse)
async def create_session(
    payload: CreateSessionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SessionDetailResponse:
    return await PracticeService(db).create_session(current_user, payload)


@router.post("/sessions/retry", response_model=SessionDetailResponse)
async def create_retry_session(
    payload: RetrySessionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SessionDetailResponse:
    from uuid import UUID

    return await PracticeService(db).create_retry_session(
        current_user, [UUID(q) for q in payload.question_ids]
    )


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SessionDetailResponse:
    return await PracticeService(db).get_session(current_user, session_id)


@router.get(
    "/sessions/{session_id}/questions/{question_number}",
    response_model=SessionQuestionResponse,
)
async def get_session_question(
    session_id: UUID,
    question_number: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SessionQuestionResponse:
    return await PracticeService(db).get_question(current_user, session_id, question_number)


@router.post(
    "/sessions/{session_id}/questions/{question_number}/answer",
    response_model=AnswerResponse,
)
async def submit_answer(
    session_id: UUID,
    question_number: int,
    payload: AnswerRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AnswerResponse:
    return await PracticeService(db).submit_answer(
        current_user, session_id, question_number, payload
    )


@router.post("/sessions/{session_id}/complete", response_model=SessionResultsResponse)
async def complete_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SessionResultsResponse:
    return await PracticeService(db).complete_session(current_user, session_id)


@router.get("/sessions/{session_id}/results", response_model=SessionResultsResponse)
async def get_session_results(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SessionResultsResponse:
    return await PracticeService(db).get_results(current_user, session_id)


@router.get("/history", response_model=HistoryResponse)
async def get_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HistoryResponse:
    return await PracticeService(db).get_history(current_user)


@router.get("/sessions/{session_id}/navigator", response_model=SessionNavigatorResponse)
async def get_session_navigator(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SessionNavigatorResponse:
    return await PracticeService(db).get_navigator(current_user, session_id)


@router.post("/sessions/{session_id}/questions/{question_number}/autosave")
async def autosave_answer(
    session_id: UUID,
    question_number: int,
    payload: AutosaveRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, bool]:
    return await PracticeService(db).autosave_answer(
        current_user, session_id, question_number, payload
    )


@router.get("/bookmarks")
async def list_bookmarks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    return await PracticeService(db).list_bookmarks(current_user)


@router.post("/questions/{question_id}/bookmark")
async def toggle_bookmark(
    question_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, bool]:
    return await PracticeService(db).toggle_bookmark(current_user, question_id)
