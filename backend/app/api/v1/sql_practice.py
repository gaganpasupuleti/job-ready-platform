from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.sql_practice import (
    SqlExecutionStatusResponse,
    SqlProblemDetail,
    SqlProgressSummary,
    SqlRunRequest,
    SqlRunResponse,
    SqlSolutionResponse,
    SqlSubmissionDetail,
    SqlSubmitResponse,
    SqlTablePreview,
    SqlTableSchemaPublic,
)
from app.services.sql_execution.executor import SqlSandboxExecutor, get_sql_executor
from app.services.sql_practice_service import SqlPracticeService

router = APIRouter(prefix="/sql")


def _sql_service(
    db: AsyncSession = Depends(get_db),
    executor: SqlSandboxExecutor = Depends(get_sql_executor),
) -> SqlPracticeService:
    return SqlPracticeService(db, executor)


@router.get("/execution-status", response_model=SqlExecutionStatusResponse)
async def execution_status(
    service: SqlPracticeService = Depends(_sql_service),
) -> SqlExecutionStatusResponse:
    return await service.execution_status_async()


@router.get("/problems")
async def list_problems(
    search: str | None = None,
    difficulty: str | None = None,
    topic_slug: str | None = None,
    tag: str | None = None,
    status: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: SqlPracticeService = Depends(_sql_service),
) -> dict:
    return await service.list_problems(
        current_user,
        search=search,
        difficulty=difficulty,
        topic_slug=topic_slug,
        tag=tag,
        status=status,
        skip=skip,
        limit=limit,
    )


@router.get("/problems/{slug_or_id}", response_model=SqlProblemDetail)
async def get_problem(
    slug_or_id: str,
    current_user: User = Depends(get_current_user),
    service: SqlPracticeService = Depends(_sql_service),
) -> SqlProblemDetail:
    return await service.get_problem(current_user, slug_or_id)


@router.get("/problems/{slug_or_id}/navigation")
async def get_problem_navigation(
    slug_or_id: str,
    current_user: User = Depends(get_current_user),
    service: SqlPracticeService = Depends(_sql_service),
):
    return await service.get_navigation(current_user, slug_or_id)


@router.get("/problems/{problem_id}/schema", response_model=list[SqlTableSchemaPublic])
async def get_schema(
    problem_id: UUID,
    current_user: User = Depends(get_current_user),
    service: SqlPracticeService = Depends(_sql_service),
) -> list[SqlTableSchemaPublic]:
    return await service.get_schema(current_user, problem_id)


@router.get("/problems/{problem_id}/tables/{table_name}/preview", response_model=SqlTablePreview)
async def preview_table(
    problem_id: UUID,
    table_name: str,
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    service: SqlPracticeService = Depends(_sql_service),
) -> SqlTablePreview:
    return await service.get_table_preview(current_user, problem_id, table_name, limit)


@router.post("/problems/{problem_id}/run", response_model=SqlRunResponse)
async def run_query(
    problem_id: UUID,
    payload: SqlRunRequest,
    current_user: User = Depends(get_current_user),
    service: SqlPracticeService = Depends(_sql_service),
) -> SqlRunResponse:
    return await service.run_query(current_user, problem_id, payload.query)


@router.post("/problems/{problem_id}/submit", response_model=SqlSubmitResponse)
async def submit_query(
    problem_id: UUID,
    payload: SqlRunRequest,
    current_user: User = Depends(get_current_user),
    service: SqlPracticeService = Depends(_sql_service),
) -> SqlSubmitResponse:
    return await service.submit_query(current_user, problem_id, payload.query)


@router.get("/submissions")
async def list_submissions(
    problem_id: UUID | None = None,
    status: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: SqlPracticeService = Depends(_sql_service),
) -> dict:
    return await service.list_submissions(
        current_user, problem_id=problem_id, status=status, skip=skip, limit=limit
    )


@router.get("/submissions/{submission_id}", response_model=SqlSubmissionDetail)
async def get_submission(
    submission_id: UUID,
    current_user: User = Depends(get_current_user),
    service: SqlPracticeService = Depends(_sql_service),
) -> SqlSubmissionDetail:
    return await service.get_submission(current_user, submission_id)


@router.get("/problems/{problem_id}/submissions")
async def problem_submissions(
    problem_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: SqlPracticeService = Depends(_sql_service),
) -> dict:
    return await service.list_submissions(
        current_user, problem_id=problem_id, skip=skip, limit=limit
    )


@router.get("/progress", response_model=SqlProgressSummary)
async def get_progress(
    current_user: User = Depends(get_current_user),
    service: SqlPracticeService = Depends(_sql_service),
) -> SqlProgressSummary:
    return await service.get_progress(current_user)


@router.post("/problems/{problem_id}/bookmark")
async def toggle_bookmark(
    problem_id: UUID,
    current_user: User = Depends(get_current_user),
    service: SqlPracticeService = Depends(_sql_service),
) -> dict[str, bool]:
    return await service.toggle_bookmark(current_user, problem_id)


@router.get("/bookmarks")
async def list_bookmarks(
    current_user: User = Depends(get_current_user),
    service: SqlPracticeService = Depends(_sql_service),
) -> list:
    return await service.list_bookmarks(current_user)


@router.get("/problems/{problem_id}/solution", response_model=SqlSolutionResponse)
async def get_solution(
    problem_id: UUID,
    current_user: User = Depends(get_current_user),
    service: SqlPracticeService = Depends(_sql_service),
) -> SqlSolutionResponse:
    return await service.get_solution(current_user, problem_id)
