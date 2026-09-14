"""Validate and apply a Saturday-style learning batch.

Dry-run does not write. Apply is local unless an explicit target confirmation
is added later. It does not publish on boot and does not write the Jobs source.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import Difficulty, QuestionType
from app.models.learn import Project, ProjectModule, ProjectTask
from app.models.learn_enums import PathAvailability, PracticePathDifficulty, ProjectTaskType
from app.models.question import Question, QuestionOption
from app.models.sql_practice import SqlExpectedResult, SqlProblem, SqlProblemColumn, SqlProblemSeedRow, SqlProblemTable
from app.models.sql_enums import SqlDialect
from app.models.studio import Assignment, ContentBatchItem, ContentPack, ContentPackQuestion, LearningMaterial
from app.models.taxonomy import Category, Domain, Topic
from app.services.job_taxonomy import JOB_FAMILIES

FAMILY_IDS = {row[0] for row in JOB_FAMILIES if row[0] != "other-review"}
LEVELS = {"beginner", "intermediate", "advanced"}


def _hash(payload: object) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def load_batch(path: Path) -> dict:
    manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))
    rejected: list[str] = []
    for item in manifest.get("items", []):
        file_path = path / item["path"]
        if not file_path.is_file():
            rejected.append(f"missing {item['path']}")
            continue
        digest = hashlib.sha256(file_path.read_bytes()).hexdigest()
        if digest != item["sha256"]:
            rejected.append(f"hash mismatch {item['path']}")
    materials = json.loads((path / "materials.json").read_text(encoding="utf-8"))["materials"]
    assignments = json.loads((path / "assignments.json").read_text(encoding="utf-8"))["assignments"]
    questions = json.loads((path / "questions.json").read_text(encoding="utf-8"))["questions"]
    packs = json.loads((path / "packs.json").read_text(encoding="utf-8"))["packs"]
    project = json.loads((path / "project.json").read_text(encoding="utf-8"))
    for material in materials:
        body = (path / material["body_file"]).read_text(encoding="utf-8")
        material["body_md"] = body
        for family in material["families"]:
            if family not in FAMILY_IDS:
                rejected.append(f"{material['key']} family {family}")
        if material["level"] not in LEVELS:
            rejected.append(f"{material['key']} level")
    keys = [row["key"] for row in questions]
    if len(keys) != len(set(keys)):
        rejected.append("duplicate question keys")
    q_by_key = {row["key"]: row for row in questions}
    for question in questions:
        correct = [opt for opt in question["options"] if opt.get("correct")]
        if not correct:
            rejected.append(f"{question['key']} has no correct option")
        if question["mode"] == "single" and len(correct) != 1:
            rejected.append(f"{question['key']} single-select count")
        if question["mode"] == "multi" and len(correct) < 2:
            rejected.append(f"{question['key']} multi-select count")
        if len({opt["key"] for opt in question["options"]}) != len(question["options"]):
            rejected.append(f"{question['key']} duplicate options")
    for pack in packs:
        for family in pack["families"]:
            if family not in FAMILY_IDS:
                rejected.append(f"{pack['key']} family {family}")
        missing = [key for key in pack["question_keys"] if key not in q_by_key]
        if missing:
            rejected.append(f"{pack['key']} unresolved {missing}")
    return {
        "batch_id": manifest["batch_id"],
        "materials": materials,
        "assignments": assignments,
        "questions": questions,
        "packs": packs,
        "project": project,
        "rejected": rejected,
        "path": path,
    }


def plan(batch: dict, stored: dict[str, ContentBatchItem]) -> dict:
    counts = {kind: {"create": 0, "update": 0, "unchanged": 0, "rejected": 0} for kind in ("material", "assignment", "question", "pack", "project")}
    actions = []
    if batch["rejected"]:
        counts["material"]["rejected"] = len(batch["rejected"])
        return {"counts": counts, "actions": [], "rejected": batch["rejected"]}
    catalog = (
        [("material", row) for row in batch["materials"]]
        + [("assignment", row) for row in batch["assignments"]]
        + [("question", row) for row in batch["questions"]]
        + [("pack", row) for row in batch["packs"]]
        + [("project", batch["project"])]
    )
    rejected = []
    for kind, row in catalog:
        key = row["key"]
        digest = _hash({k: v for k, v in row.items() if k != "body_md"} | ({"body_md": row.get("body_md")} if kind == "material" else {}))
        version = int(row.get("version") or 1)
        previous = stored.get(key)
        if previous is None:
            action = "create"
        elif previous.content_hash == digest and previous.version == version:
            action = "unchanged"
        elif version > previous.version:
            action = "update"
        else:
            action = "rejected"
            rejected.append(f"{key} changed without a version bump")
        counts[kind][action] += 1
        actions.append({"key": key, "type": kind, "action": action, "version": version, "hash": digest})
    return {"counts": counts, "actions": actions, "rejected": rejected}


def _difficulty(value: str) -> Difficulty:
    return {"easy": Difficulty.EASY, "medium": Difficulty.MEDIUM, "hard": Difficulty.HARD}[value]


async def _topic(db: AsyncSession, slug: str, name: str) -> Topic:
    domain = (await db.execute(select(Domain).where(Domain.slug == "jobready-studio"))).scalar_one_or_none()
    if domain is None:
        domain = Domain(name="JobReady studio", slug="jobready-studio", description="Authored learning batch", is_active=True)
        db.add(domain)
        await db.flush()
    category = (await db.execute(select(Category).where(Category.slug == "studio-practice", Category.domain_id == domain.id))).scalar_one_or_none()
    if category is None:
        category = Category(domain_id=domain.id, name="Studio practice", slug="studio-practice", is_active=True)
        db.add(category)
        await db.flush()
    topic = (await db.execute(select(Topic).where(Topic.slug == slug, Topic.category_id == category.id))).scalar_one_or_none()
    if topic is None:
        topic = Topic(category_id=category.id, name=name, slug=slug, is_active=True)
        db.add(topic)
        await db.flush()
    return topic


async def _shop_tables(db, problem: SqlProblem) -> None:
    customers = SqlProblemTable(problem_id=problem.id, table_name="customers", description="Shop customers", sort_order=0)
    orders = SqlProblemTable(problem_id=problem.id, table_name="orders", description="One row per order", sort_order=1)
    payments = SqlProblemTable(problem_id=problem.id, table_name="payments", description="Payments that exist", sort_order=2)
    db.add_all([customers, orders, payments])
    await db.flush()
    db.add_all([
        SqlProblemColumn(table_id=customers.id, column_name="id", data_type="int", is_nullable=False, sort_order=0),
        SqlProblemColumn(table_id=customers.id, column_name="name", data_type="text", is_nullable=False, sort_order=1),
        SqlProblemColumn(table_id=customers.id, column_name="city", data_type="text", is_nullable=False, sort_order=2),
        SqlProblemColumn(table_id=orders.id, column_name="id", data_type="int", is_nullable=False, sort_order=0),
        SqlProblemColumn(table_id=orders.id, column_name="customer_id", data_type="int", is_nullable=False, sort_order=1),
        SqlProblemColumn(table_id=orders.id, column_name="status", data_type="text", is_nullable=False, sort_order=2),
        SqlProblemColumn(table_id=orders.id, column_name="amount", data_type="numeric", is_nullable=True, sort_order=3),
        SqlProblemColumn(table_id=orders.id, column_name="ordered_on", data_type="date", is_nullable=False, sort_order=4),
        SqlProblemColumn(table_id=payments.id, column_name="id", data_type="int", is_nullable=False, sort_order=0),
        SqlProblemColumn(table_id=payments.id, column_name="order_id", data_type="int", is_nullable=False, sort_order=1),
        SqlProblemColumn(table_id=payments.id, column_name="amount", data_type="numeric", is_nullable=False, sort_order=2),
        SqlProblemColumn(table_id=payments.id, column_name="paid_on", data_type="date", is_nullable=False, sort_order=3),
        SqlProblemSeedRow(table_id=customers.id, row_data={"id": 1, "name": "Ada", "city": "Hyderabad"}, sort_order=0),
        SqlProblemSeedRow(table_id=customers.id, row_data={"id": 2, "name": "Ben", "city": "Bengaluru"}, sort_order=1),
        SqlProblemSeedRow(table_id=customers.id, row_data={"id": 3, "name": "Cho", "city": "Pune"}, sort_order=2),
        SqlProblemSeedRow(table_id=orders.id, row_data={"id": 1, "customer_id": 1, "status": "paid", "amount": 1000, "ordered_on": "2026-01-02"}, sort_order=0),
        SqlProblemSeedRow(table_id=orders.id, row_data={"id": 2, "customer_id": 1, "status": "pending", "amount": 500, "ordered_on": "2026-01-05"}, sort_order=1),
        SqlProblemSeedRow(table_id=orders.id, row_data={"id": 3, "customer_id": 2, "status": "paid", "amount": 800, "ordered_on": "2026-01-03"}, sort_order=2),
        SqlProblemSeedRow(table_id=orders.id, row_data={"id": 4, "customer_id": 2, "status": "cancelled", "amount": 200, "ordered_on": "2026-01-04"}, sort_order=3),
        SqlProblemSeedRow(table_id=orders.id, row_data={"id": 5, "customer_id": 3, "status": "shipped", "amount": 1500, "ordered_on": "2026-01-06"}, sort_order=4),
        SqlProblemSeedRow(table_id=payments.id, row_data={"id": 1, "order_id": 1, "amount": 1000, "paid_on": "2026-01-02"}, sort_order=0),
        SqlProblemSeedRow(table_id=payments.id, row_data={"id": 2, "order_id": 3, "amount": 800, "paid_on": "2026-01-04"}, sort_order=1),
    ])


SQL_PROBLEMS = {
    "orders-paid-totals": {
        "title": "Paid order totals",
        "task": "Return one row: paid_orders and paid_amount for status = 'paid'. Do not treat a missing amount as zero.",
        "solution": "SELECT COUNT(*) AS paid_orders, SUM(amount) AS paid_amount FROM orders WHERE status = 'paid'",
        "columns": ["paid_orders", "paid_amount"],
        "rows": [[2, 1800]],
    },
    "orders-missing-payment": {
        "title": "Orders with no payment row",
        "task": "Return missing_payments, the number of orders with no payment row. Use IS NULL.",
        "solution": "SELECT COUNT(*) AS missing_payments FROM orders o LEFT JOIN payments p ON p.order_id = o.id WHERE p.id IS NULL",
        "columns": ["missing_payments"],
        "rows": [[3]],
    },
    "orders-revenue-by-customer": {
        "title": "Revenue by customer excluding cancelled",
        "task": "Return customer_name and revenue for non-cancelled orders, ordered by customer_name.",
        "solution": "SELECT c.name AS customer_name, SUM(o.amount) AS revenue FROM customers c JOIN orders o ON o.customer_id = c.id WHERE o.status <> 'cancelled' GROUP BY c.name ORDER BY c.name",
        "columns": ["customer_name", "revenue"],
        "rows": [["Ada", 1500], ["Ben", 800], ["Cho", 1500]],
    },
}


async def _upsert_sql(db: AsyncSession, topic: Topic, slug: str) -> SqlProblem:
    spec = SQL_PROBLEMS[slug]
    problem = (await db.execute(select(SqlProblem).where(SqlProblem.slug == slug))).scalar_one_or_none()
    if problem is None:
        category = await db.get(Category, topic.category_id)
        problem = SqlProblem(
            slug=slug,
            title=spec["title"],
            description="Synthetic shop dataset. PostgreSQL. Amounts are rupees. This is not an employer question.",
            difficulty=Difficulty.EASY,
            database_dialect=SqlDialect.POSTGRESQL,
            domain_id=category.domain_id,
            category_id=topic.category_id,
            topic_id=topic.id,
            tags=["sql"],
            role_tags=["data-analyst", "data-engineer"],
            scenario="Orders and payments for a small shop.",
            task_description=spec["task"],
            expected_columns=spec["columns"],
            solution_query=spec["solution"],
            solution_explanation="Hand-checked against the five orders and two payments.",
            hints=["Read the status values before aggregating."],
            sample_expected_rows=spec["rows"],
            is_active=True,
            is_sample=True,
            order_sensitive=slug == "orders-revenue-by-customer",
        )
        # domain_id must be the domain, not the category. Load it.
        category = await db.get(Category, topic.category_id)
        problem.domain_id = category.domain_id
        db.add(problem)
        await db.flush()
        await _shop_tables(db, problem)
        db.add(SqlExpectedResult(problem_id=problem.id, columns=spec["columns"], rows=spec["rows"]))
        await db.flush()
    return problem


async def apply_batch(db: AsyncSession, path: Path, *, allow_remote: bool = False) -> dict:
    database_url = ""
    bind = db.get_bind()
    if bind is not None:
        database_url = str(bind.url)
    host = (urlparse(database_url.replace("+asyncpg", "")).hostname or "").lower()
    if not allow_remote and host not in {"localhost", "127.0.0.1", ""}:
        return {"refused": True, "reason": "target is not a local application database"}
    batch = load_batch(path)
    stored_rows = (await db.execute(select(ContentBatchItem))).scalars().all()
    stored = {row.item_key: row for row in stored_rows}
    planned = plan(batch, stored)
    if planned["rejected"] or batch["rejected"]:
        return {"refused": True, "rejected": planned["rejected"] or batch["rejected"], "counts": planned["counts"]}
    topic = await _topic(db, "studio-saturday-001", "Saturday batch 001")
    now = datetime.now(UTC)
    for action in planned["actions"]:
        if action["action"] == "unchanged":
            continue
        kind, key = action["type"], action["key"]
        if kind == "material":
            row = next(item for item in batch["materials"] if item["key"] == key)
            current = (await db.execute(select(LearningMaterial).where(LearningMaterial.content_key == key))).scalar_one_or_none()
            payload = dict(
                version=action["version"],
                title=row["title"],
                summary=row["summary"],
                kind=row["kind"],
                level=row["level"],
                audience=row.get("audience"),
                estimated_minutes=row["minutes"],
                objectives=row["objectives"],
                prerequisites=row["prerequisites"],
                body_md=row["body_md"],
                examples=row["examples"],
                exercises=row["exercises"],
                summary_md=row["summary"],
                sources=row["sources"],
                families=row["families"],
                skill_tags=row["skills"],
                download_relpath=row["body_file"],
                content_hash=action["hash"],
                is_published=True,
            )
            if current is None:
                db.add(LearningMaterial(content_key=key, **payload))
            else:
                for field, value in payload.items():
                    setattr(current, field, value)
        elif kind == "question":
            row = next(item for item in batch["questions"] if item["key"] == key)
            current = (
                await db.execute(select(Question).options(selectinload(Question.options)).where(Question.content_key == key))
            ).scalar_one_or_none()
            explanation = row["explanation"] + " " + " ".join(f"{opt['key']}: {opt['why']}" for opt in row["options"])
            if current is None:
                current = Question(
                    content_key=key,
                    question_type=QuestionType.MULTIPLE_CHOICE if row["mode"] == "multi" else QuestionType.SINGLE_CHOICE,
                    title=key,
                    question_text=row["stem"],
                    explanation=explanation,
                    difficulty=_difficulty(row["difficulty"]),
                    domain_id=(await db.get(Category, topic.category_id)).domain_id,
                    category_id=topic.category_id,
                    topic_id=topic.id,
                    is_active=True,
                )
                db.add(current)
                await db.flush()
            else:
                current.question_text = row["stem"]
                current.explanation = explanation
                current.difficulty = _difficulty(row["difficulty"])
                current.question_type = QuestionType.MULTIPLE_CHOICE if row["mode"] == "multi" else QuestionType.SINGLE_CHOICE
                for option in list(current.options):
                    await db.delete(option)
                await db.flush()
            for index, opt in enumerate(row["options"]):
                db.add(QuestionOption(question_id=current.id, option_text=opt["text"], is_correct=bool(opt["correct"]), sort_order=index))
        elif kind == "assignment":
            row = next(item for item in batch["assignments"] if item["key"] == key)
            current = (await db.execute(select(Assignment).where(Assignment.content_key == key))).scalar_one_or_none()
            payload = dict(
                version=action["version"],
                title=row["title"],
                goal=row["goal"],
                brief_md=row["brief"],
                requirements=row["requirements"],
                deliverables=row["deliverables"],
                hints=row["hints"],
                prerequisites=row["prerequisites"],
                rubric=row["rubric"],
                submission_mode=row["mode"],
                estimated_minutes=row["minutes"],
                due_at=None,
                families=row["families"],
                skill_tags=row["skills"],
                sql_problem_slug=row.get("sql_problem_slug"),
                content_hash=action["hash"],
                is_published=True,
            )
            if current is None:
                db.add(Assignment(content_key=key, **payload))
            else:
                for field, value in payload.items():
                    setattr(current, field, value)
        if kind == "pack":
            continue
        record = stored.get(key) or ContentBatchItem(item_key=key)
        record.content_type = kind
        record.version = action["version"]
        record.content_hash = action["hash"]
        record.batch_id = batch["batch_id"]
        record.applied_at = now
        stored[key] = record
        db.add(record)
    await db.flush()
    sql_ids = {}
    for slug in SQL_PROBLEMS:
        problem = await _upsert_sql(db, topic, slug)
        sql_ids[slug] = problem.id
    project_row = batch["project"]
    project = (await db.execute(select(Project).where(Project.slug == project_row["key"]))).scalar_one_or_none()
    if project is None:
        project = Project(
            slug=project_row["key"],
            title=project_row["title"],
            short_description=project_row["outcome"][:500],
            description=project_row["scenario"],
            difficulty=PracticePathDifficulty.BEGINNER,
            technology="sql",
            category_key="sql",
            estimated_minutes=90,
            is_published=True,
            availability=PathAvailability.AVAILABLE,
            prerequisites=[],
            skills=project_row["skills"],
            final_objective=project_row["outcome"],
            reference_json={"families": project_row["families"], "dataset": "dataset.sql"},
        )
        db.add(project)
        await db.flush()
        module = ProjectModule(project_id=project.id, title="Payment quality", sort_order=0)
        db.add(module)
        await db.flush()
        for index, milestone in enumerate(project_row["milestones"]):
            task_type = ProjectTaskType.SQL if milestone["type"] == "sql" else ProjectTaskType.REVIEW
            db.add(
                ProjectTask(
                    module_id=module.id,
                    title=milestone["title"],
                    sort_order=index,
                    task_type=task_type,
                    sql_problem_id=sql_ids.get(milestone.get("sql_problem_slug")),
                    summary=milestone["deliverable"],
                    body_json={"note": "SQL milestones require an accepted studio submission. The findings note is not an automatic grade."},
                    checklist_json=[],
                )
            )
    for pack_row in batch["packs"]:
        pack = (await db.execute(select(ContentPack).where(ContentPack.content_key == pack_row["key"]))).scalar_one_or_none()
        if pack is None:
            pack = ContentPack(
                content_key=pack_row["key"],
                version=1,
                title=pack_row["title"],
                kind=pack_row["kind"],
                instructions=pack_row["instructions"],
                families=pack_row["families"],
                skill_tags=[],
                question_count=len(pack_row["question_keys"]),
                content_hash=_hash(pack_row),
                is_published=True,
            )
            db.add(pack)
            await db.flush()
        else:
            pack.title = pack_row["title"]
            pack.instructions = pack_row["instructions"]
            pack.families = pack_row["families"]
            pack.question_count = len(pack_row["question_keys"])
            pack.is_published = True
        existing_links = (await db.execute(select(ContentPackQuestion).where(ContentPackQuestion.pack_id == pack.id))).scalars().all()
        for link in existing_links:
            await db.delete(link)
        await db.flush()
        for index, question_key in enumerate(pack_row["question_keys"]):
            question = (await db.execute(select(Question).where(Question.content_key == question_key))).scalar_one()
            db.add(ContentPackQuestion(pack_id=pack.id, question_id=question.id, sort_order=index))
        record = stored.get(pack_row["key"]) or ContentBatchItem(item_key=pack_row["key"])
        record.content_type = "pack"
        record.version = 1
        record.content_hash = _hash(pack_row)
        record.batch_id = batch["batch_id"]
        record.applied_at = now
        db.add(record)
    await db.commit()
    return {"refused": False, "counts": planned["counts"], "rejected": []}
