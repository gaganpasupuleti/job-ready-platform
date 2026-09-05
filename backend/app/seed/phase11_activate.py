"""Phase 11: activate original aptitude + technical MCQs for production coverage.

Usage:
  python -m app.seed.phase11_activate
"""

from __future__ import annotations

import asyncio
from uuid import uuid4

from sqlalchemy import select

from app.content.hashing import content_hash
from app.db.session import AsyncSessionLocal, engine
from app.models.enums import Difficulty, QuestionType
from app.models.question import Question, QuestionOption
from app.models.taxonomy import Category, Domain, Topic
from app.seed.phase11_aptitude_mcq import APTITUDE_MCQS
from app.seed.phase11_technical_mcq import TECHNICAL_MCQS


async def seed_phase11_mcqs() -> tuple[int, int]:
    """Insert Phase 11 MCQs idempotently. Returns (created, skipped)."""
    created = 0
    skipped = 0
    rows = list(APTITUDE_MCQS) + list(TECHNICAL_MCQS)

    async with AsyncSessionLocal() as session:
        existing_texts = list((await session.execute(select(Question.question_text))).scalars().all())
        existing_text_set = set(existing_texts)
        existing_hashes = {content_hash(t) for t in existing_texts}

        domains = {d.slug: d for d in (await session.execute(select(Domain))).scalars().all()}
        categories = {
            (c.domain_id, c.slug): c for c in (await session.execute(select(Category))).scalars().all()
        }
        topics = {
            (t.category_id, t.slug): t for t in (await session.execute(select(Topic))).scalars().all()
        }

        for (
            domain_slug,
            cat_slug,
            topic_slug,
            difficulty,
            text,
            expl,
            correct,
            w1,
            w2,
            w3,
        ) in rows:
            digest = content_hash(text)
            if text in existing_text_set or digest in existing_hashes:
                skipped += 1
                continue

            domain = domains.get(domain_slug)
            if domain is None:
                print(f"SKIP missing domain slug={domain_slug!r}")
                skipped += 1
                continue
            category = categories.get((domain.id, cat_slug))
            if category is None:
                print(f"SKIP missing category domain={domain_slug!r} category={cat_slug!r}")
                skipped += 1
                continue
            topic = topics.get((category.id, topic_slug))
            if topic is None:
                print(
                    f"SKIP missing topic domain={domain_slug!r} category={cat_slug!r} topic={topic_slug!r}"
                )
                skipped += 1
                continue

            question = Question(
                question_type=QuestionType.SINGLE_CHOICE,
                question_text=text,
                explanation=expl,
                difficulty=Difficulty(difficulty),
                domain_id=domain.id,
                category_id=category.id,
                topic_id=topic.id,
                marks=1.0,
                negative_marks=0.25,
                estimated_time_seconds=90,
                is_active=True,
                is_premium=False,
                is_sample=True,
            )
            session.add(question)
            await session.flush()
            for idx, (opt, ok) in enumerate([(correct, True), (w1, False), (w2, False), (w3, False)]):
                session.add(
                    QuestionOption(
                        id=uuid4(),
                        question_id=question.id,
                        option_text=opt,
                        is_correct=ok,
                        sort_order=idx,
                    )
                )
            existing_text_set.add(text)
            existing_hashes.add(digest)
            created += 1

        await session.commit()

    print(f"Phase 11 MCQs: created={created} skipped={skipped}")
    return created, skipped


async def _main() -> None:
    try:
        await seed_phase11_mcqs()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(_main())
