"""Student-facing Practice Hub, course, lesson, and project routes."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.learn import (
    ContinueLearningItem,
    CourseDetail,
    CourseListItem,
    LessonDetail,
    LessonFeedbackIn,
    PracticeHubResponse,
    PracticePathCard,
    PracticePathDetail,
    ProjectCard,
    ProjectDetail,
    SearchResponse,
)
from app.services.learn_service import LearnService

router = APIRouter()


@router.get("/practice-hub", response_model=PracticeHubResponse, tags=["learn"])
async def practice_hub(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PracticeHubResponse:
    return await LearnService(db).practice_hub(user)


@router.get("/paths", response_model=list[PracticePathCard], tags=["learn"])
async def list_paths(
    path_type: str | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[PracticePathCard]:
    return await LearnService(db).list_paths(user, path_type=path_type)


@router.get("/paths/{slug}", response_model=PracticePathDetail, tags=["learn"])
async def get_path(
    slug: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PracticePathDetail:
    return await LearnService(db).get_path(slug, user)


@router.get("/courses", response_model=list[CourseListItem], tags=["learn"])
async def list_courses(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[CourseListItem]:
    return await LearnService(db).list_courses(user)


@router.get("/courses/{slug}", response_model=CourseDetail, tags=["learn"])
async def get_course(
    slug: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CourseDetail:
    return await LearnService(db).get_course(slug, user)


@router.get(
    "/courses/{course_slug}/modules/{module_slug}/lessons/{lesson_slug}",
    response_model=LessonDetail,
    tags=["learn"],
)
async def get_lesson(
    course_slug: str,
    module_slug: str,
    lesson_slug: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LessonDetail:
    return await LearnService(db).get_lesson(course_slug, module_slug, lesson_slug, user)


@router.post("/lessons/{lesson_id}/start", tags=["learn"])
async def start_lesson(
    lesson_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await LearnService(db).start_lesson(lesson_id, user)


@router.post("/lessons/{lesson_id}/complete", tags=["learn"])
async def complete_lesson(
    lesson_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await LearnService(db).complete_lesson(lesson_id, user)


@router.post("/lessons/{lesson_id}/attempt", tags=["learn"])
async def record_attempt(
    lesson_id: UUID,
    payload: dict[str, Any] = Body(default_factory=dict),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await LearnService(db).record_attempt(lesson_id, user, payload)


@router.post("/lessons/{lesson_id}/feedback", tags=["learn"])
async def lesson_feedback(
    lesson_id: UUID,
    payload: LessonFeedbackIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await LearnService(db).feedback(lesson_id, user, payload)


@router.get("/projects", response_model=list[ProjectCard], tags=["learn"])
async def list_projects(
    category_key: str | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ProjectCard]:
    return await LearnService(db).list_projects(user, category_key=category_key)


@router.get("/projects/{slug}", response_model=ProjectDetail, tags=["learn"])
async def get_project(
    slug: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectDetail:
    return await LearnService(db).get_project(slug, user)


@router.get("/learning/continue", response_model=list[ContinueLearningItem], tags=["learn"])
async def continue_learning(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ContinueLearningItem]:
    return await LearnService(db).continue_learning(user)


@router.get("/practice/search", response_model=SearchResponse, tags=["learn"])
async def practice_search(
    q: str = Query(default="", max_length=120),
    limit: int = Query(default=20, ge=1, le=50),
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SearchResponse:
    return await LearnService(db).search(q, limit=limit)
