from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.coding import (
    CodingProblemDetail,
    CodingProblemListItem,
    CodingProblemListResponse,
    CodingProgressSummary,
    ExecutionResponse,
    ExecutionStatusResponse,
    RunSubmitRequest,
    SubmissionDetail,
    SubmissionListResponse,
)
from app.services.code_execution.interface import CodeExecutionService, get_code_execution_service
from app.services.code_execution.languages import list_languages
from app.services.code_execution.health import get_execution_health
from app.services.coding_service import CodingService

router = APIRouter(prefix="/coding")


def _coding_service(
    db: AsyncSession = Depends(get_db),
    executor: CodeExecutionService = Depends(get_code_execution_service),
) -> CodingService:
    return CodingService(db, executor)


@router.get("/execution-status", response_model=ExecutionStatusResponse)
async def execution_status(
    service: CodingService = Depends(_coding_service),
) -> ExecutionStatusResponse:
    return await service.get_execution_status()


@router.get("/languages")
async def get_languages() -> list[dict]:
    snap = await get_execution_health()
    if snap.languages:
        return [
            {
                "id": lang["id"],
                "name": lang["name"],
                "key": lang.get("key"),
                "available": bool(lang.get("available", True)),
            }
            for lang in snap.languages
        ]
    return [
        {
            "id": lang.id,
            "name": lang.name,
            "key": lang.key,
            "available": lang.available,
        }
        for lang in list_languages()
    ]


@router.get("/problems", response_model=CodingProblemListResponse)
async def list_problems(
    domain_id: UUID | None = None,
    topic_id: UUID | None = None,
    topic_slug: str | None = None,
    difficulty: str | None = None,
    search: str | None = None,
    tag: str | None = None,
    language_id: int | None = None,
    progress_status: str | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    user: User = Depends(get_current_user),
    service: CodingService = Depends(_coding_service),
) -> CodingProblemListResponse:
    return await service.list_problems(
        user,
        domain_id=domain_id,
        topic_id=topic_id,
        topic_slug=topic_slug,
        difficulty=difficulty,
        search=search,
        tag=tag,
        language_id=language_id,
        progress_status=progress_status,
        skip=skip,
        limit=limit,
    )


@router.get("/problems/{problem_id}", response_model=CodingProblemDetail)
async def get_problem(
    problem_id: UUID,
    user: User = Depends(get_current_user),
    service: CodingService = Depends(_coding_service),
) -> CodingProblemDetail:
    return await service.get_problem(user, problem_id)


@router.get("/problems/{problem_id}/navigation")
async def get_problem_navigation(
    problem_id: UUID,
    user: User = Depends(get_current_user),
    service: CodingService = Depends(_coding_service),
):
    return await service.get_navigation(user, problem_id)


@router.post("/problems/{problem_id}/run", response_model=ExecutionResponse)
async def run_code(
    problem_id: UUID,
    payload: RunSubmitRequest,
    user: User = Depends(get_current_user),
    service: CodingService = Depends(_coding_service),
    db: AsyncSession = Depends(get_db),
) -> ExecutionResponse:
    result = await service.run_code(user, problem_id, payload)
    await db.commit()
    return result


@router.post("/problems/{problem_id}/submit", response_model=ExecutionResponse)
async def submit_code(
    problem_id: UUID,
    payload: RunSubmitRequest,
    user: User = Depends(get_current_user),
    service: CodingService = Depends(_coding_service),
) -> ExecutionResponse:
    return await service.submit_code(user, problem_id, payload)


@router.post("/problems/{problem_id}/bookmark")
async def toggle_bookmark(
    problem_id: UUID,
    user: User = Depends(get_current_user),
    service: CodingService = Depends(_coding_service),
) -> dict[str, bool]:
    return await service.toggle_bookmark(user, problem_id)


@router.get("/bookmarks", response_model=list[CodingProblemListItem])
async def list_bookmarks(
    user: User = Depends(get_current_user),
    service: CodingService = Depends(_coding_service),
) -> list[CodingProblemListItem]:
    return await service.list_bookmarks(user)


@router.get("/submissions", response_model=SubmissionListResponse)
async def list_submissions(
    problem_id: UUID | None = None,
    status: str | None = None,
    language_id: int | None = None,
    difficulty: str | None = None,
    search: str | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    user: User = Depends(get_current_user),
    service: CodingService = Depends(_coding_service),
) -> SubmissionListResponse:
    return await service.list_submissions(
        user,
        problem_id=problem_id,
        status=status,
        language_id=language_id,
        difficulty=difficulty,
        search=search,
        skip=skip,
        limit=limit,
    )


@router.get("/submissions/{submission_id}", response_model=SubmissionDetail)
async def get_submission(
    submission_id: UUID,
    user: User = Depends(get_current_user),
    service: CodingService = Depends(_coding_service),
) -> SubmissionDetail:
    return await service.get_submission(user, submission_id)


@router.get("/progress", response_model=CodingProgressSummary)
async def get_progress(
    user: User = Depends(get_current_user),
    service: CodingService = Depends(_coding_service),
) -> CodingProgressSummary:
    return await service.get_progress_summary(user)
