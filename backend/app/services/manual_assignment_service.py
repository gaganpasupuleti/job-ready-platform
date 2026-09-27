"""Manual assignment submissions. Links are stored for a later human review."""

from __future__ import annotations

from urllib.parse import urlparse
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.learn import Project
from app.models.manual_assignment import AWAITING_REVIEW, REVIEWED, ManualAssignmentSubmission
from app.models.user import User


def normalize_https_link(value: str) -> str:
    link = (value or "").strip()
    parsed = urlparse(link)
    if parsed.scheme != "https" or not parsed.netloc or any(ch.isspace() for ch in link):
        raise AppException("Submit an https link, such as a GitHub repository.", status_code=400)
    if len(link) > 500:
        raise AppException("Link is too long.", status_code=400)
    return link


def link_kind(link: str) -> str:
    host = urlparse(link).netloc.lower()
    if host == "github.com" or host.endswith(".github.com"):
        return "github"
    return "link"


class ManualAssignmentService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def submit(
        self,
        user: User,
        *,
        title: str,
        link: str,
        note: str | None,
        question: str | None,
        project_id: UUID | None,
    ) -> dict:
        clean_title = title.strip()
        if len(clean_title) < 3 or len(clean_title) > 160:
            raise AppException("Title must be between 3 and 160 characters.", status_code=400)
        clean_link = normalize_https_link(link)
        clean_note = (note or "").strip() or None
        clean_question = (question or "").strip() or None
        if clean_note and len(clean_note) > 2000:
            raise AppException("Note is too long.", status_code=400)
        if clean_question and len(clean_question) > 2000:
            raise AppException("Question is too long.", status_code=400)
        if project_id is not None:
            project = await self.db.get(Project, project_id)
            if project is None or not project.is_published:
                raise AppException("Project not found", status_code=404)
        row = ManualAssignmentSubmission(
            user_id=user.id,
            project_id=project_id,
            title=clean_title,
            link=clean_link,
            note=clean_note,
            question=clean_question,
            status=AWAITING_REVIEW,
        )
        self.db.add(row)
        await self.db.commit()
        await self.db.refresh(row)
        project_title = await self._project_title(row.project_id)
        return self._report(row, user, project_title)

    async def list_for_user(self, user: User) -> list[dict]:
        rows = (
            await self.db.execute(
                select(ManualAssignmentSubmission)
                .where(ManualAssignmentSubmission.user_id == user.id)
                .order_by(ManualAssignmentSubmission.created_at.desc())
            )
        ).scalars().all()
        titles = await self._project_titles([row.project_id for row in rows])
        return [self._report(row, user, titles.get(row.project_id)) for row in rows]

    async def review_queue(self) -> list[dict]:
        rows = (
            await self.db.execute(
                select(ManualAssignmentSubmission, User)
                .join(User, User.id == ManualAssignmentSubmission.user_id)
                .order_by(ManualAssignmentSubmission.created_at.desc())
            )
        ).all()
        titles = await self._project_titles([row.project_id for row, _user in rows])
        return [self._report(row, user, titles.get(row.project_id)) for row, user in rows]

    async def save_review(self, submission_id: UUID, review_note: str) -> dict:
        note = review_note.strip()
        if len(note) < 3:
            raise AppException("Add a short review note.", status_code=400)
        row = await self.db.get(ManualAssignmentSubmission, submission_id)
        if row is None:
            raise AppException("Submission not found", status_code=404)
        user = await self.db.get(User, row.user_id)
        if user is None:
            raise AppException("Submission not found", status_code=404)
        row.review_note = note
        row.status = REVIEWED
        await self.db.commit()
        await self.db.refresh(row)
        project_title = await self._project_title(row.project_id)
        return self._report(row, user, project_title)

    async def _project_title(self, project_id: UUID | None) -> str | None:
        if project_id is None:
            return None
        project = await self.db.get(Project, project_id)
        return project.title if project else None

    async def _project_titles(self, project_ids: list[UUID | None]) -> dict[UUID, str]:
        ids = [project_id for project_id in project_ids if project_id is not None]
        if not ids:
            return {}
        rows = (await self.db.execute(select(Project).where(Project.id.in_(ids)))).scalars().all()
        return {project.id: project.title for project in rows}

    def _report(self, row: ManualAssignmentSubmission, user: User, project_title: str | None) -> dict:
        return {
            "id": str(row.id),
            "student_name": user.full_name or user.username,
            "student_email": user.email,
            "title": row.title,
            "link": row.link,
            "kind": link_kind(row.link),
            "note": row.note,
            "question": row.question,
            "project_id": str(row.project_id) if row.project_id else None,
            "project_title": project_title,
            "status": row.status,
            "review_note": row.review_note,
            "graded": False,
            "submitted_at": row.created_at.isoformat() if row.created_at else None,
        }
