"""Idempotent coding problem seed for Build 3.1."""

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.coding import CodingProblem, CodingTestCase
from app.models.taxonomy import Category, Domain, Topic
from app.models.user import User
from app.seed.problems_bank import ALL_LANG_IDS, PROBLEM_BANK

EXTRA_TOPICS = [
    ("hash-maps", "Hash Maps"),
    ("stack", "Stack"),
    ("queue", "Queue"),
    ("searching", "Searching"),
    ("sorting", "Sorting"),
    ("recursion", "Recursion"),
    ("linked-lists", "Linked Lists"),
    ("trees", "Trees"),
    ("two-pointers", "Two Pointers"),
    ("sliding-window", "Sliding Window"),
    ("binary-search", "Binary Search"),
    ("dynamic-programming", "Dynamic Programming"),
]


async def ensure_dsa_taxonomy(session) -> dict:
    domain = (await session.execute(select(Domain).where(Domain.slug == "technical"))).scalar_one()
    category = (
        await session.execute(
            select(Category).where(Category.domain_id == domain.id, Category.slug == "dsa")
        )
    ).scalar_one_or_none()
    if category is None:
        category = Category(domain_id=domain.id, name="DSA", slug="dsa", is_active=True)
        session.add(category)
        await session.flush()

    topics: dict[str, Topic] = {}
    for slug, name in [
        ("basics", "Basics"),
        ("arrays", "Arrays"),
        ("strings", "Strings"),
        *EXTRA_TOPICS,
    ]:
        topic = (
            await session.execute(
                select(Topic).where(Topic.category_id == category.id, Topic.slug == slug)
            )
        ).scalar_one_or_none()
        if topic is None:
            topic = Topic(category_id=category.id, name=name, slug=slug, is_active=True)
            session.add(topic)
            await session.flush()
        topics[slug] = topic
    return {"domain": domain, "category": category, "topics": topics}


async def seed_coding_problems() -> None:
    async with AsyncSessionLocal() as session:
        admin = (
            await session.execute(select(User).where(User.email == "admin@jobready.dev"))
        ).scalar_one_or_none()
        taxonomy = await ensure_dsa_taxonomy(session)
        created = 0
        skipped = 0

        for item in PROBLEM_BANK:
            existing = (
                await session.execute(select(CodingProblem).where(CodingProblem.slug == item["slug"]))
            ).scalar_one_or_none()
            if existing:
                skipped += 1
                continue

            topic = taxonomy["topics"].get(item["topic"])
            if topic is None:
                topic = taxonomy["topics"]["basics"]

            problem = CodingProblem(
                slug=item["slug"],
                title=item["title"],
                description=item["description"],
                difficulty=item["difficulty"],
                domain_id=taxonomy["domain"].id,
                category_id=taxonomy["category"].id,
                topic_id=topic.id,
                constraints=item.get("constraints"),
                input_format=item.get("input_format"),
                output_format=item.get("output_format"),
                tags=item.get("tags", []),
                supported_language_ids=ALL_LANG_IDS,
                starter_code=item["starter_code"],
                is_active=True,
                is_sample=True,
                created_by=admin.id if admin else None,
                test_cases=[CodingTestCase(**tc) for tc in item["test_cases"]],
            )
            session.add(problem)
            created += 1

        await session.commit()
        total = (
            await session.execute(select(CodingProblem))
        ).scalars().all()
        print(f"Coding seed: created={created}, skipped={skipped}, total={len(total)}")
