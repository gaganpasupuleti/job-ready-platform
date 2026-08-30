"""Publish approved interview Q&A from a validated payload into the live bank."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.content.hashing import content_hash, slug_from_question
from app.content.validator import ValidationResult, validate_question_payload
from app.models.enums import Difficulty
from app.models.interview import (
    InterviewAnswerPoint,
    InterviewQuestion,
    InterviewQuestionCompany,
    InterviewQuestionJob,
    InterviewQuestionRole,
    InterviewQuestionSkill,
)
from app.models.interview_enums import (
    ContentReviewStatus,
    ContentSourceType,
    ExperienceLevel,
    InterviewQuestionType,
)


async def unique_slug(session: AsyncSession, question_text: str) -> str:
    base = slug_from_question(question_text)
    slug = base
    n = 2
    while True:
        exists = await session.execute(
            select(InterviewQuestion.id).where(InterviewQuestion.slug == slug)
        )
        if exists.scalar_one_or_none() is None:
            return slug
        slug = f"{base}-{n}"
        n += 1


async def publish_validated_question(
    session: AsyncSession,
    payload: dict[str, Any],
    *,
    validation: ValidationResult | None = None,
    source_type: ContentSourceType = ContentSourceType.CURSOR_GENERATED,
    reviewer_id: uuid.UUID | None = None,
) -> InterviewQuestion:
    result = validation or await validate_question_payload(session, payload)
    if not result.ok:
        raise ValueError("; ".join(result.errors))

    resolved = result.resolved
    digest = result.content_hash or content_hash(resolved["question_text"])
    existing = await session.execute(
        select(InterviewQuestion).where(InterviewQuestion.content_hash == digest)
    )
    found = existing.scalar_one_or_none()
    if found is not None:
        return found

    question = InterviewQuestion(
        slug=await unique_slug(session, resolved["question_text"]),
        question_text=resolved["question_text"],
        question_type=InterviewQuestionType(resolved["question_type"]),
        difficulty=Difficulty(resolved["difficulty"]),
        experience_level=ExperienceLevel(resolved["experience_level"]),
        expected_answer=resolved["expected_answer"],
        explanation=resolved["explanation"],
        source_type=source_type,
        review_status=ContentReviewStatus.APPROVED,
        content_hash=digest,
        is_active=True,
        domain_id=resolved["domain"].id if resolved["domain"] else None,
        category_id=resolved["category"].id if resolved["category"] else None,
        topic_id=resolved["topic"].id if resolved["topic"] else None,
        reviewed_at=datetime.now(UTC),
        reviewed_by=reviewer_id,
    )
    session.add(question)
    await session.flush()

    for idx, point in enumerate(resolved["key_points"]):
        session.add(
            InterviewAnswerPoint(question_id=question.id, point_text=point, sort_order=idx)
        )
    for skill in resolved["skills"]:
        session.add(InterviewQuestionSkill(question_id=question.id, skill_id=skill.id))
    for role in resolved["roles"]:
        session.add(InterviewQuestionRole(question_id=question.id, role_id=role.id))
    for company in resolved["companies"]:
        session.add(InterviewQuestionCompany(question_id=question.id, company_id=company.id))
    for job in resolved["jobs"]:
        session.add(InterviewQuestionJob(question_id=question.id, job_id=job.id))
    await session.flush()
    return question
