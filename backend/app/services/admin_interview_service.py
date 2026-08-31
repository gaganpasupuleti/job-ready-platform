"""Admin interview pack management."""

from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.interview import (
    InterviewPack,
    InterviewPackQuestion,
    InterviewQuestion,
)
from app.models.interview_enums import ContentReviewStatus
from app.models.tagging import Company, JobRole
from app.schemas.interview import InterviewPackPublic
from app.schemas.interview_session import AdminInterviewPackCreate, AdminInterviewPackUpdate
from app.services.interview_session_service import _slugify


class AdminInterviewPackService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _resolve_role(self, name: str | None) -> UUID | None:
        if not name:
            return None
        row = (
            await self.db.execute(
                select(JobRole).where((JobRole.slug == _slugify(name)) | (JobRole.name.ilike(name)))
            )
        ).scalar_one_or_none()
        if not row:
            raise AppException(f"Unknown role: {name}", status_code=400)
        return row.id

    async def _resolve_company(self, name: str | None) -> UUID | None:
        if not name:
            return None
        row = (
            await self.db.execute(
                select(Company).where((Company.slug == _slugify(name)) | (Company.name.ilike(name)))
            )
        ).scalar_one_or_none()
        if not row:
            raise AppException(f"Unknown company: {name}", status_code=400)
        return row.id

    async def _validate_questions(self, question_ids: list[UUID]) -> list[UUID]:
        if not question_ids:
            return []
        rows = (
            await self.db.execute(
                select(InterviewQuestion).where(InterviewQuestion.id.in_(question_ids))
            )
        ).scalars().all()
        by_id = {r.id: r for r in rows}
        ordered: list[UUID] = []
        for qid in question_ids:
            q = by_id.get(qid)
            if not q:
                raise AppException(f"Question not found: {qid}", status_code=400)
            if q.review_status != ContentReviewStatus.APPROVED or not q.is_active:
                raise AppException(
                    f"Question {q.slug} must be approved and active",
                    status_code=400,
                )
            if qid not in ordered:
                ordered.append(qid)
        return ordered

    async def _count(self, pack_id: UUID) -> int:
        return int(
            (
                await self.db.execute(
                    select(func.count())
                    .select_from(InterviewPackQuestion)
                    .where(InterviewPackQuestion.pack_id == pack_id)
                )
            ).scalar_one()
            or 0
        )

    async def list_packs(self) -> list[InterviewPackPublic]:
        packs = (
            await self.db.execute(select(InterviewPack).order_by(InterviewPack.title))
        ).scalars().all()
        out: list[InterviewPackPublic] = []
        for p in packs:
            out.append(
                InterviewPackPublic(
                    id=p.id,
                    slug=p.slug,
                    title=p.title,
                    description=p.description,
                    experience_level=p.experience_level,
                    question_count=await self._count(p.id),
                )
            )
        return out

    async def create(self, payload: AdminInterviewPackCreate) -> InterviewPackPublic:
        slug = payload.slug or _slugify(payload.title)
        exists = (
            await self.db.execute(select(InterviewPack).where(InterviewPack.slug == slug))
        ).scalar_one_or_none()
        if exists:
            raise AppException("Pack slug already exists", status_code=400)
        qids = await self._validate_questions(payload.question_ids)
        if payload.is_active and len(qids) < 3:
            raise AppException("Active packs require at least 3 approved questions", status_code=400)
        if not payload.title.strip() or not (payload.description or "").strip():
            if payload.is_active:
                raise AppException("Active packs require title and description", status_code=400)
        pack = InterviewPack(
            id=uuid4(),
            slug=slug,
            title=payload.title.strip(),
            description=payload.description,
            experience_level=payload.experience_level,
            target_role_id=await self._resolve_role(payload.target_role),
            target_company_id=await self._resolve_company(payload.target_company),
            is_active=payload.is_active,
        )
        self.db.add(pack)
        await self.db.flush()
        for i, qid in enumerate(qids):
            self.db.add(InterviewPackQuestion(pack_id=pack.id, question_id=qid, sort_order=i))
        await self.db.commit()
        return InterviewPackPublic(
            id=pack.id,
            slug=pack.slug,
            title=pack.title,
            description=pack.description,
            experience_level=pack.experience_level,
            question_count=len(qids),
        )

    async def update(self, pack_id: UUID, payload: AdminInterviewPackUpdate) -> InterviewPackPublic:
        pack = await self.db.get(InterviewPack, pack_id)
        if not pack:
            raise AppException("Pack not found", status_code=404)
        if payload.title is not None:
            pack.title = payload.title.strip()
        if payload.description is not None:
            pack.description = payload.description
        if payload.experience_level is not None:
            pack.experience_level = payload.experience_level
        if payload.target_role is not None:
            pack.target_role_id = await self._resolve_role(payload.target_role)
        if payload.target_company is not None:
            pack.target_company_id = await self._resolve_company(payload.target_company)
        if payload.question_ids is not None:
            qids = await self._validate_questions(payload.question_ids)
            existing = (
                await self.db.execute(
                    select(InterviewPackQuestion).where(InterviewPackQuestion.pack_id == pack.id)
                )
            ).scalars().all()
            for link in existing:
                await self.db.delete(link)
            await self.db.flush()
            for i, qid in enumerate(qids):
                self.db.add(InterviewPackQuestion(pack_id=pack.id, question_id=qid, sort_order=i))
        if payload.is_active is not None:
            count = (
                len(payload.question_ids)
                if payload.question_ids is not None
                else await self._count(pack.id)
            )
            if payload.is_active:
                if count < 3:
                    raise AppException(
                        "Active packs require at least 3 approved questions",
                        status_code=400,
                    )
                if not pack.title or not pack.description:
                    raise AppException("Active packs require title and description", status_code=400)
            pack.is_active = payload.is_active
        await self.db.commit()
        return InterviewPackPublic(
            id=pack.id,
            slug=pack.slug,
            title=pack.title,
            description=pack.description,
            experience_level=pack.experience_level,
            question_count=await self._count(pack.id),
        )
