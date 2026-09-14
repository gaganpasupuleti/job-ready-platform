"""Freeze the brief a student or reviewer already has.

A later content version may edit the live assignment or milestone. That edit
must not rewrite a filed submission or an in-progress attempt. Expected SQL
answers are not stored here.
"""

from __future__ import annotations


def assignment_brief_snapshot(assignment) -> dict:
    return {
        "title": assignment.title,
        "goal": assignment.goal,
        "brief_md": assignment.brief_md,
        "requirements": list(assignment.requirements or []),
        "rubric": list(assignment.rubric or []),
        "version": assignment.version,
    }


def task_brief_snapshot(task, version: int | None = None) -> dict:
    return {
        "title": task.title,
        "summary": task.summary,
        "body_json": dict(task.body_json or {}),
        "checklist_json": list(task.checklist_json or []),
        "version": version,
    }


async def freeze_assignment_submissions(db, assignment) -> None:
    """Copy the current brief onto submissions that do not already have one."""
    from sqlalchemy import select

    from app.models.studio import AssignmentSubmission

    rows = (
        await db.execute(
            select(AssignmentSubmission).where(AssignmentSubmission.assignment_id == assignment.id)
        )
    ).scalars().all()
    snapshot = assignment_brief_snapshot(assignment)
    for row in rows:
        if row.brief_snapshot:
            continue
        row.brief_snapshot = snapshot


async def freeze_task_progress(db, task, version: int | None) -> None:
    """Copy the current milestone text onto progress rows before an in-place edit."""
    from sqlalchemy import select

    from app.models.learn import UserProjectTaskProgress

    rows = (
        await db.execute(
            select(UserProjectTaskProgress).where(UserProjectTaskProgress.task_id == task.id)
        )
    ).scalars().all()
    snapshot = task_brief_snapshot(task, version)
    for row in rows:
        if row.brief_snapshot:
            continue
        row.brief_snapshot = snapshot
