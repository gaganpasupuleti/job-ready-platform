"""Explicit runtime locks. Do not infer these from titles or descriptions."""

from __future__ import annotations

PYTHON_LANGUAGE_ID = 71
PYTHON_LOCK_MESSAGE = (
    "Python is locked for this release. Previous submissions and reviews are unchanged. "
    "New submissions are not accepted."
)
PYTHON_MILESTONE_NOTE = (
    "A Python milestone is locked for this release. Other milestones stay available. "
    "This project cannot be completed until that milestone returns."
)


def assignment_requires_python(mode: str | None, requires_runtime: str | None = None) -> bool:
    """local_python and requires_runtime=python are authored metadata, not title keywords."""
    if (mode or "") == "local_python":
        return True
    return (requires_runtime or "").strip().lower() == "python"


def task_requires_python(body_json: dict | None, task_type: str | None = None) -> bool:
    body = body_json or {}
    if str(body.get("requires_runtime") or "").strip().lower() == "python":
        return True
    return str(task_type or "").strip().lower() == "python"
