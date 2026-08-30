
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.interview import (
    InterviewPackPublic,
    InterviewQuestionListResponse,
    InterviewQuestionPublic,
)
from app.services.interview_content_service import InterviewContentService

router = APIRouter(prefix="/interview")


@router.get("/questions", response_model=InterviewQuestionListResponse)
async def list_interview_questions(
    role: str | None = None,
    skill: str | None = None,
    difficulty: str | None = None,
    question_type: str | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InterviewQuestionListResponse:
    return await InterviewContentService(db).list_public(
        role=role,
        skill=skill,
        difficulty=difficulty,
        question_type=question_type,
        skip=skip,
        limit=limit,
    )


@router.get("/questions/{slug_or_id}", response_model=InterviewQuestionPublic)
async def get_interview_question(
    slug_or_id: str,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InterviewQuestionPublic:
    return await InterviewContentService(db).get_public(slug_or_id)


@router.get("/packs", response_model=list[InterviewPackPublic])
async def list_interview_packs(
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[InterviewPackPublic]:
    return await InterviewContentService(db).list_packs()
