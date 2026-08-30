"""Admin authoring routes for Practice Hub paths, courses, modules, and lessons."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Body, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.learn import (
    CourseAdminIn,
    LessonAdminIn,
    ModuleAdminIn,
    PracticePathAdminIn,
)
from app.services.learn_service import LearnAdminService

router = APIRouter(prefix="/admin")


@router.get("/practice-paths")
async def list_practice_paths(
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    return await LearnAdminService(db).list_paths()


@router.post("/practice-paths", status_code=201)
async def create_practice_path(
    payload: PracticePathAdminIn,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await LearnAdminService(db).create_path(payload)


@router.patch("/practice-paths/{path_id}")
async def update_practice_path(
    path_id: UUID,
    payload: dict[str, Any] = Body(default_factory=dict),
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await LearnAdminService(db).update_path(path_id, payload)


@router.get("/courses")
async def list_courses(
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    return await LearnAdminService(db).list_courses()


@router.post("/courses", status_code=201)
async def create_course(
    payload: CourseAdminIn,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await LearnAdminService(db).create_course(payload)


@router.patch("/courses/{course_id}")
async def update_course(
    course_id: UUID,
    payload: dict[str, Any] = Body(default_factory=dict),
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await LearnAdminService(db).update_course(course_id, payload)


@router.post("/courses/{course_id}/modules", status_code=201)
async def create_module(
    course_id: UUID,
    payload: ModuleAdminIn,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await LearnAdminService(db).create_module(course_id, payload)


@router.post("/modules/{module_id}/lessons", status_code=201)
async def create_lesson(
    module_id: UUID,
    payload: LessonAdminIn,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await LearnAdminService(db).create_lesson(module_id, payload)


@router.patch("/lessons/{lesson_id}")
async def update_lesson(
    lesson_id: UUID,
    payload: dict[str, Any] = Body(default_factory=dict),
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await LearnAdminService(db).update_lesson(lesson_id, payload)
