"""Mark linked project tasks complete when an engine challenge is solved."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.learn import Project, ProjectModule, ProjectTask, UserProjectProgress, UserProjectTaskProgress
from app.models.learn_enums import ProgressStatus


def _now() -> datetime:
    return datetime.now(UTC)


async def complete_linked_project_tasks(
    db: AsyncSession,
    user_id: UUID,
    *,
    coding_problem_id: UUID | None = None,
    sql_problem_id: UUID | None = None,
    topic_id: UUID | None = None,
    scenario_slug: str | None = None,
) -> None:
    stmt = select(ProjectTask)
    if coding_problem_id:
        stmt = stmt.where(ProjectTask.coding_problem_id == coding_problem_id)
    elif sql_problem_id:
        stmt = stmt.where(ProjectTask.sql_problem_id == sql_problem_id)
    elif topic_id:
        stmt = stmt.where(ProjectTask.topic_id == topic_id)
    elif scenario_slug:
        stmt = stmt.where(
            (ProjectTask.scenario_slug == scenario_slug)
            | (ProjectTask.summary.contains(scenario_slug))
            | (ProjectTask.title.contains(scenario_slug))
        )
    else:
        return
    tasks = (await db.execute(stmt)).scalars().all()
    if not tasks:
        return
    for task in tasks:
        await _complete_task_row(db, user_id, task)
    await _refresh_project_percents(db, user_id, [t.module_id for t in tasks])


async def _complete_task_row(db: AsyncSession, user_id: UUID, task: ProjectTask) -> None:
    row = (
        await db.execute(
            select(UserProjectTaskProgress).where(
                UserProjectTaskProgress.user_id == user_id,
                UserProjectTaskProgress.task_id == task.id,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        row = UserProjectTaskProgress(user_id=user_id, task_id=task.id)
        db.add(row)
    if row.status == ProgressStatus.COMPLETED:
        return
    row.status = ProgressStatus.COMPLETED
    row.completed_at = row.completed_at or _now()
    row.last_activity_at = _now()


async def _refresh_project_percents(db: AsyncSession, user_id: UUID, module_ids: list[UUID]) -> None:
    if not module_ids:
        return
    projects = (
        await db.execute(
            select(Project)
            .options(selectinload(Project.modules).selectinload(ProjectModule.tasks))
            .join(ProjectModule, ProjectModule.project_id == Project.id)
            .where(ProjectModule.id.in_(module_ids))
        )
    ).scalars().unique().all()
    for project in projects:
        ordered = [task for module in project.modules for task in module.tasks]
        if not ordered:
            continue
        completed = (
            await db.execute(
                select(UserProjectTaskProgress.task_id).where(
                    UserProjectTaskProgress.user_id == user_id,
                    UserProjectTaskProgress.task_id.in_([t.id for t in ordered]),
                    UserProjectTaskProgress.status == ProgressStatus.COMPLETED,
                )
            )
        ).scalars().all()
        percent = int(round(len(set(completed)) * 100 / len(ordered)))
        progress = (
            await db.execute(
                select(UserProjectProgress).where(
                    UserProjectProgress.user_id == user_id,
                    UserProjectProgress.project_id == project.id,
                )
            )
        ).scalar_one_or_none()
        if progress is None:
            progress = UserProjectProgress(user_id=user_id, project_id=project.id)
            db.add(progress)
        progress.percent = percent
        progress.last_activity_at = _now()
        progress.status = ProgressStatus.COMPLETED if percent >= 100 else ProgressStatus.IN_PROGRESS
        if percent >= 100:
            progress.completed_at = progress.completed_at or _now()
