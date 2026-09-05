"""Phase 12: activate data-platform + AI/infra MCQs with taxonomy ensure.

Usage:
  python -m app.seed.phase12_activate
"""

from __future__ import annotations

import asyncio
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.content.hashing import content_hash
from app.db.session import AsyncSessionLocal, engine
from app.models.enums import Difficulty, QuestionType
from app.models.question import Question, QuestionOption
from app.models.taxonomy import Category, Domain, Topic
from app.seed.phase12_ai_infra_mcq import AI_INFRA_MCQS
from app.seed.phase12_data_mcq import DATA_PLATFORM_MCQS

# domain_slug -> category_slug -> (category_name, [(topic_slug, topic_name), ...])
TAXONOMY_ENSURE: dict[str, dict[str, tuple[str, list[tuple[str, str]]]]] = {
    "technical": {
        "data-engineering": (
            "Data Engineering",
            [
                ("etl", "ETL"),
                ("streaming", "Streaming"),
                ("data-modeling", "Data Modeling"),
                ("data-quality", "Data Quality"),
                ("lakehouse", "Lakehouse"),
            ],
        ),
        "snowflake": (
            "Snowflake",
            [
                ("fundamentals", "Fundamentals"),
                ("warehouses", "Warehouses"),
                ("security", "Security"),
            ],
        ),
        "spark": (
            "Spark",
            [
                ("fundamentals", "Fundamentals"),
                ("performance", "Performance"),
                ("sql", "SQL"),
            ],
        ),
        "flink": (
            "Flink",
            [
                ("fundamentals", "Fundamentals"),
                ("event-time", "Event Time"),
            ],
        ),
        "databricks": (
            "Databricks",
            [
                ("delta-lake", "Delta Lake"),
                ("unity-catalog", "Unity Catalog"),
            ],
        ),
        "power-bi": (
            "Power BI",
            [
                ("dax", "DAX"),
                ("modeling", "Modeling"),
            ],
        ),
        "servicenow": (
            "ServiceNow",
            [
                ("incident-lifecycle", "Incident Lifecycle"),
                ("reporting", "Reporting"),
            ],
        ),
        "azure-data": (
            "Azure Data",
            [
                ("adf", "Azure Data Factory"),
                ("synapse", "Synapse"),
            ],
        ),
    },
    "cloud": {
        "aws": (
            "AWS",
            [
                ("s3", "S3"),
                ("glue", "Glue"),
                ("iam", "IAM"),
            ],
        ),
    },
    "ai": {
        "generative-ai": (
            "Generative AI",
            [
                ("embeddings", "Embeddings"),
                ("vector-databases", "Vector Databases"),
                ("tool-calling", "Tool Calling"),
                ("rag", "RAG"),
                ("ai-security", "AI Security"),
            ],
        ),
        "ai-agents": (
            "AI Agents",
            [
                ("agent-fundamentals", "Agent Fundamentals"),
                ("agent-loops", "Agent Loops"),
                ("mcp-fundamentals", "MCP Fundamentals"),
                ("multi-agent-systems", "Multi-Agent Systems"),
            ],
        ),
    },
    "devops": {
        "docker": (
            "Docker",
            [
                ("images", "Images"),
                ("dockerfile", "Dockerfile"),
                ("layers", "Layers"),
                ("volumes", "Volumes"),
                ("compose", "Compose"),
                ("multi-stage", "Multi-stage Builds"),
                ("docker-networks", "Docker Networks"),
                ("health-checks", "Health Checks"),
                ("container-security", "Container Security"),
            ],
        ),
        "kubernetes": (
            "Kubernetes",
            [
                ("deployment", "Deployment"),
                ("service", "Service"),
                ("probes", "Probes"),
                ("requests-limits", "Requests and Limits"),
                ("pvc", "Persistent Volume Claims"),
                ("autoscaling", "Autoscaling"),
                ("k8s-secrets", "Secrets"),
                ("k8s-rbac", "RBAC"),
                ("k8s-troubleshooting", "Troubleshooting"),
            ],
        ),
    },
}


async def _ensure_domain(session: AsyncSession, slug: str, name: str | None = None) -> Domain | None:
    domain = (await session.execute(select(Domain).where(Domain.slug == slug))).scalar_one_or_none()
    if domain is not None:
        return domain
    # Phase 12 does not create top-level domains; they must already exist from prior seeds.
    print(f"SKIP missing domain slug={slug!r} (create via base taxonomy seed first)")
    return None


async def ensure_phase12_taxonomy(session: AsyncSession) -> None:
    """Create missing categories/topics used by Phase 12 MCQs."""
    domains = {d.slug: d for d in (await session.execute(select(Domain))).scalars().all()}
    categories = {
        (c.domain_id, c.slug): c for c in (await session.execute(select(Category))).scalars().all()
    }
    topics = {
        (t.category_id, t.slug): t for t in (await session.execute(select(Topic))).scalars().all()
    }

    created_cats = 0
    created_topics = 0

    for domain_slug, cats in TAXONOMY_ENSURE.items():
        domain = domains.get(domain_slug)
        if domain is None:
            domain = await _ensure_domain(session, domain_slug)
            if domain is None:
                continue
            domains[domain_slug] = domain

        for cat_slug, (cat_name, topic_rows) in cats.items():
            category = categories.get((domain.id, cat_slug))
            if category is None:
                category = Category(
                    name=cat_name,
                    slug=cat_slug,
                    domain_id=domain.id,
                    is_active=True,
                )
                session.add(category)
                await session.flush()
                categories[(domain.id, cat_slug)] = category
                created_cats += 1
                print(f"Created category domain={domain_slug!r} category={cat_slug!r}")

            for topic_slug, topic_name in topic_rows:
                topic = topics.get((category.id, topic_slug))
                if topic is None:
                    topic = Topic(
                        name=topic_name,
                        slug=topic_slug,
                        category_id=category.id,
                        is_active=True,
                    )
                    session.add(topic)
                    await session.flush()
                    topics[(category.id, topic_slug)] = topic
                    created_topics += 1
                    print(
                        f"Created topic domain={domain_slug!r} category={cat_slug!r} topic={topic_slug!r}"
                    )

    await session.flush()
    print(f"Phase 12 taxonomy ensure: categories_created={created_cats} topics_created={created_topics}")


async def seed_phase12_mcqs() -> tuple[int, int]:
    """Insert Phase 12 MCQs idempotently. Returns (created, skipped)."""
    created = 0
    skipped = 0
    rows = list(DATA_PLATFORM_MCQS) + list(AI_INFRA_MCQS)

    async with AsyncSessionLocal() as session:
        await ensure_phase12_taxonomy(session)

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

    print(f"Phase 12 MCQs: created={created} skipped={skipped}")
    return created, skipped


async def _main() -> None:
    try:
        await seed_phase12_mcqs()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(_main())
