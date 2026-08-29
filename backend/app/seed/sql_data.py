"""Idempotent SQL practice problem seed for Build 4."""

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.enums import Difficulty
from app.models.sql_enums import SqlDialect
from app.models.sql_practice import (
    SqlExpectedResult,
    SqlProblem,
    SqlProblemColumn,
    SqlProblemSeedRow,
    SqlProblemTable,
)
from app.models.taxonomy import Category, Domain, Topic
from app.models.user import User
from app.seed.sql_problems_bank import SQL_PROBLEM_BANK, SQL_TOPICS


async def ensure_sql_taxonomy(session) -> dict:
    domain = (await session.execute(select(Domain).where(Domain.slug == "technical"))).scalar_one()
    category = (
        await session.execute(
            select(Category).where(Category.domain_id == domain.id, Category.slug == "sql")
        )
    ).scalar_one_or_none()
    if category is None:
        category = Category(domain_id=domain.id, name="SQL", slug="sql", is_active=True)
        session.add(category)
        await session.flush()

    topics: dict[str, Topic] = {}
    for slug, name in SQL_TOPICS:
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


def _build_tables(table_defs: list[dict]) -> list[SqlProblemTable]:
    tables: list[SqlProblemTable] = []
    for t_idx, tdef in enumerate(table_defs):
        table = SqlProblemTable(
            table_name=tdef["table_name"],
            display_name=tdef.get("display_name"),
            description=tdef.get("description"),
            sort_order=tdef.get("sort_order", t_idx),
            columns=[
                SqlProblemColumn(
                    column_name=col["column_name"],
                    data_type=col["data_type"],
                    is_nullable=col.get("is_nullable", True),
                    sort_order=col.get("sort_order", c_idx),
                )
                for c_idx, col in enumerate(tdef.get("columns", []))
            ],
            seed_rows=[
                SqlProblemSeedRow(
                    row_data=row,
                    sort_order=r_idx,
                    is_sample=True,
                )
                for r_idx, row in enumerate(tdef.get("rows", []))
            ],
        )
        tables.append(table)
    return tables


async def seed_sql_problems() -> None:
    async with AsyncSessionLocal() as session:
        admin = (
            await session.execute(select(User).where(User.email == "admin@jobready.dev"))
        ).scalar_one_or_none()
        taxonomy = await ensure_sql_taxonomy(session)
        created = 0
        skipped = 0

        for item in SQL_PROBLEM_BANK:
            existing = (
                await session.execute(select(SqlProblem).where(SqlProblem.slug == item["slug"]))
            ).scalar_one_or_none()
            if existing:
                skipped += 1
                continue

            topic_slug = item["topic_slug"]
            topic = taxonomy["topics"].get(topic_slug)
            if topic is None:
                topic = taxonomy["topics"]["sql-fundamentals"]

            difficulty = item["difficulty"]
            if not isinstance(difficulty, Difficulty):
                difficulty = Difficulty(difficulty)

            problem = SqlProblem(
                slug=item["slug"],
                title=item["title"],
                description=item["description"],
                difficulty=difficulty,
                database_dialect=SqlDialect.POSTGRESQL,
                domain_id=taxonomy["domain"].id,
                category_id=taxonomy["category"].id,
                topic_id=topic.id,
                tags=item.get("tags", []),
                role_tags=item.get("role_tags", []),
                scenario=item.get("scenario"),
                task_description=item["task_description"],
                expected_columns=item["expected_columns"],
                order_sensitive=item.get("order_sensitive", False),
                solution_query=item["solution_query"],
                solution_explanation=item.get("solution_explanation"),
                alternate_solution=item.get("alternate_solution"),
                key_concepts=item.get("key_concepts", []),
                hints=item.get("hints", []),
                sample_expected_rows=item.get("sample_expected_rows", []),
                estimated_time_seconds=item.get("estimated_time_seconds", 300),
                is_active=True,
                is_sample=True,
                created_by=admin.id if admin else None,
                tables=_build_tables(item.get("tables", [])),
                expected_result=SqlExpectedResult(
                    columns=item["expected_columns"],
                    rows=item["expected_rows"],
                ),
            )
            session.add(problem)
            created += 1

        await session.commit()
        total = (await session.execute(select(SqlProblem))).scalars().all()
        print(f"SQL seed: created={created}, skipped={skipped}, total={len(total)}")
