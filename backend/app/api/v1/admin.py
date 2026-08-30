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
    TaxonomyTopicCreate,
    TaxonomyTopicUpdate,
)
from app.schemas.coding import (
    AdminCodingProblemCreate,
    AdminCodingProblemDetail,
    AdminCodingProblemListResponse,
    AdminCodingProblemUpdate,
    AdminTestCaseCreate,
    AdminTestCaseDetail,
    AdminTestCaseUpdate,
)
from app.schemas.practice import CatalogResponse
from app.services.admin_question_service import AdminQuestionService
from app.services.catalog_service import CatalogService
from app.services.coding_service import AdminCodingService
from app.services.sql_practice_service import AdminSqlPracticeService
from app.schemas.sql_practice import (
    AdminSqlProblemCreate,
    AdminSqlProblemDetail,
    AdminSqlProblemListResponse,
    AdminSqlProblemUpdate,
    AdminSqlValidateResponse,
)

router = APIRouter(prefix="/admin")


@router.get("/taxonomy", response_model=CatalogResponse)
async def get_taxonomy(
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> CatalogResponse:
    return await CatalogService(db).get_catalog(use_cache=False)


@router.post("/taxonomy/topics")
async def create_taxonomy_topic(
    payload: TaxonomyTopicCreate,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    return await CatalogService(db).create_topic(payload)


@router.patch("/taxonomy/topics/{topic_id}")
async def update_taxonomy_topic(
    topic_id: UUID,
    payload: TaxonomyTopicUpdate,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    return await CatalogService(db).update_topic(topic_id, payload)


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


@router.get("/coding/problems", response_model=AdminCodingProblemListResponse)
async def list_coding_problems(
    domain_id: UUID | None = None,
    search: str | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminCodingProblemListResponse:
    return await AdminCodingService(db).list_problems(
        domain_id=domain_id, search=search, skip=skip, limit=limit
    )


@router.get("/coding/problems/{problem_id}", response_model=AdminCodingProblemDetail)
async def get_coding_problem(
    problem_id: UUID,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminCodingProblemDetail:
    return await AdminCodingService(db).get_problem(problem_id)


@router.post("/coding/problems", response_model=AdminCodingProblemDetail)
async def create_coding_problem(
    payload: AdminCodingProblemCreate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminCodingProblemDetail:
    return await AdminCodingService(db).create_problem(admin, payload)


@router.put("/coding/problems/{problem_id}", response_model=AdminCodingProblemDetail)
async def update_coding_problem(
    problem_id: UUID,
    payload: AdminCodingProblemUpdate,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminCodingProblemDetail:
    return await AdminCodingService(db).update_problem(problem_id, payload)


@router.delete("/coding/problems/{problem_id}")
async def delete_coding_problem(
    problem_id: UUID,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await AdminCodingService(db).delete_problem(problem_id)
    return {"ok": True}


@router.post("/coding/problems/{problem_id}/test-cases", response_model=AdminTestCaseDetail)
async def add_coding_test_case(
    problem_id: UUID,
    payload: AdminTestCaseCreate,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminTestCaseDetail:
    return await AdminCodingService(db).add_test_case(problem_id, payload)


@router.put("/coding/test-cases/{test_case_id}", response_model=AdminTestCaseDetail)
async def update_coding_test_case(
    test_case_id: UUID,
    payload: AdminTestCaseUpdate,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminTestCaseDetail:
    return await AdminCodingService(db).update_test_case(test_case_id, payload)


@router.delete("/coding/test-cases/{test_case_id}")
async def delete_coding_test_case(
    test_case_id: UUID,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await AdminCodingService(db).delete_test_case(test_case_id)
    return {"ok": True}


@router.get("/sql/problems", response_model=AdminSqlProblemListResponse)
async def list_sql_problems(
    search: str | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminSqlProblemListResponse:
    return await AdminSqlPracticeService(db).list_problems(search=search, skip=skip, limit=limit)


@router.get("/sql/problems/{problem_id}", response_model=AdminSqlProblemDetail)
async def get_sql_problem(
    problem_id: UUID,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminSqlProblemDetail:
    return await AdminSqlPracticeService(db).get_problem(problem_id)


@router.post("/sql/problems", response_model=AdminSqlProblemDetail)
async def create_sql_problem(
    payload: AdminSqlProblemCreate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminSqlProblemDetail:
    return await AdminSqlPracticeService(db).create_problem(admin, payload)


@router.put("/sql/problems/{problem_id}", response_model=AdminSqlProblemDetail)
async def update_sql_problem(
    problem_id: UUID,
    payload: AdminSqlProblemUpdate,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminSqlProblemDetail:
    return await AdminSqlPracticeService(db).update_problem(problem_id, payload)


@router.delete("/sql/problems/{problem_id}")
async def delete_sql_problem(
    problem_id: UUID,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await AdminSqlPracticeService(db).delete_problem(problem_id)
    return {"ok": True}


@router.post("/sql/problems/{problem_id}/validate", response_model=AdminSqlValidateResponse)
async def validate_sql_problem(
    problem_id: UUID,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminSqlValidateResponse:
    return await AdminSqlPracticeService(db).validate_problem(problem_id)
