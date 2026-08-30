"""Import generated JSON into content_generation_candidates (not live by default)."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.content.publisher import publish_validated_question
from app.content.validator import validate_file_payload
from app.models.interview import ContentGenerationBatch, ContentGenerationCandidate
from app.models.interview_enums import (
    ContentBatchStatus,
    ContentReviewStatus,
    ContentSourceType,
    ContentType,
    ContentValidationStatus,
)


async def import_questions_file(
    session: AsyncSession,
    path: Path,
    *,
    approve: bool = False,
    target_skill: str | None = None,
    target_role: str | None = None,
    target_company: str | None = None,
    target_domain: str | None = None,
) -> ContentGenerationBatch:
    raw = json.loads(path.read_text(encoding="utf-8"))
    results, questions = await validate_file_payload(session, raw)

    batch = ContentGenerationBatch(
        id=uuid4(),
        batch_date=date.today(),
        content_type=ContentType.INTERVIEW_QA,
        target_domain=target_domain or raw.get("target_domain"),
        target_role=target_role or raw.get("target_role"),
        target_skill=target_skill or raw.get("target_skill"),
        target_company=target_company or raw.get("target_company"),
        requested_count=len(questions),
        generated_count=len(questions),
        accepted_count=0,
        rejected_count=0,
        status=ContentBatchStatus.IMPORTED,
        generator="cursor",
        source_filename=path.name,
    )
    session.add(batch)
    await session.flush()

    accepted = 0
    rejected = 0
    for payload, validation in zip(questions, results, strict=True):
        candidate = ContentGenerationCandidate(
            id=uuid4(),
            batch_id=batch.id,
            content_type=ContentType.INTERVIEW_QA,
            payload_json=payload if isinstance(payload, dict) else {"invalid": payload},
            content_hash=validation.content_hash or "invalid",
            validation_status=(
                ContentValidationStatus.VALID if validation.ok else ContentValidationStatus.INVALID
            ),
            review_status=ContentReviewStatus.PENDING,
            validation_errors=validation.as_json(),
        )
        session.add(candidate)
        await session.flush()
        if approve and validation.ok:
            question = await publish_validated_question(
                session,
                payload,
                validation=validation,
                source_type=ContentSourceType.CURSOR_GENERATED,
            )
            candidate.review_status = ContentReviewStatus.APPROVED
            candidate.published_question_id = question.id
            accepted += 1
        elif not validation.ok:
            rejected += 1

    batch.accepted_count = accepted
    batch.rejected_count = rejected
    if approve:
        batch.status = ContentBatchStatus.COMPLETED
        batch.completed_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(batch)
    return batch


def summarize_import(batch: ContentGenerationBatch) -> dict[str, Any]:
    return {
        "batch_id": str(batch.id),
        "source_filename": batch.source_filename,
        "generated_count": batch.generated_count,
        "accepted_count": batch.accepted_count,
        "status": batch.status.value if hasattr(batch.status, "value") else batch.status,
    }
