from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.admin import (
    AdminQuestionCreate,
    AdminQuestionDetail,
    AdminQuestionListResponse,
    AdminQuestionUpdate,
)
from app.schemas.practice import CatalogResponse
from app.services.admin_question_service import AdminQuestionService
from app.services.catalog_service import CatalogService

router = APIRouter(prefix="/admin")


@router.get("/taxonomy", response_model=CatalogResponse)
async def get_taxonomy(
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> CatalogResponse:
    return await CatalogService(db).get_catalog(use_cache=False)


@router.get("/questions", response_model=AdminQuestionListResponse)
async def list_questions(
    domain_id: UUID | None = None,
    category_id: UUID | None = None,
    topic_id: UUID | None = None,
    search: str | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminQuestionListResponse:
    return await AdminQuestionService(db).list_questions(
        domain_id=domain_id,
        category_id=category_id,
        topic_id=topic_id,
        search=search,
        skip=skip,
        limit=limit,
    )


@router.get("/questions/{question_id}", response_model=AdminQuestionDetail)
async def get_question(
    question_id: UUID,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminQuestionDetail:
    return await AdminQuestionService(db).get_question(question_id)


@router.post("/questions", response_model=AdminQuestionDetail)
async def create_question(
    payload: AdminQuestionCreate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminQuestionDetail:
    return await AdminQuestionService(db).create_question(admin, payload)


@router.put("/questions/{question_id}", response_model=AdminQuestionDetail)
async def update_question(
    question_id: UUID,
    payload: AdminQuestionUpdate,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminQuestionDetail:
    return await AdminQuestionService(db).update_question(question_id, payload)
