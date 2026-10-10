"""Disposable-database checks for the CRT and DSA sprint batch."""

from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.content.studio_batch import apply_batch, load_batch
from app.db.session import AsyncSessionLocal
from app.models.enums import Difficulty, QuestionType
from app.models.practice import Bookmark
from app.models.question import Question, QuestionOption
from app.models.taxonomy import Category, Domain, Topic
from app.models.user import User
from app.seed.coding_data import ensure_dsa_taxonomy
from app.seed.taxonomy_data import TAXONOMY

BATCH = Path(__file__).resolve().parents[1] / "content" / "batches" / "2026-10-10-crt-dsa-sprint-001"
LAPTOP = "A laptop listed at ₹40,000 is offered at 15% off. What is the sale price?"


def test_batch_shape_and_independent_arithmetic():
    batch = load_batch(BATCH)
    assert batch["rejected"] == []
    assert batch["batch_id"] == "2026-10-10-crt-dsa-sprint-001"
    assert len(batch["questions"]) == 70
    by_skill: dict[str, int] = {}
    for question in batch["questions"]:
        by_skill[question["skill"]] = by_skill.get(question["skill"], 0) + 1
        correct = [opt for opt in question["options"] if opt["correct"]]
        assert len(correct) == 1
        assert "Correct answer:" in question["explanation"]
        assert "Step-by-step" in question["explanation"]
        assert "Why other options are wrong" in question["explanation"]
        assert "Learn the concept" in question["explanation"]
        assert "Formula or key principle" in question["explanation"]
        assert "Worked example" in question["explanation"]
        assert "Related lesson" in question["explanation"]
        assert "Topic metadata" in question["explanation"]
        if question["skill"] in {"arrays", "strings", "complexity", "searching"}:
            assert "Worked algorithm" in question["explanation"]
            assert "Dry run" in question["explanation"]
    assert by_skill == {
        "quantitative": 10,
        "logical-reasoning": 10,
        "verbal": 10,
        "data-interpretation": 10,
        "arrays": 10,
        "strings": 10,
        "complexity": 5,
        "searching": 5,
    }
    assert 40000 - (40000 * 15 / 100) == 34000
    assert 45 / 180 * 360 == 90
    assert 16 / (12 + 8 + 16 + 4) == 0.4
    assert 4 * 5 / 2 == 10
    low, high = 0, 5
    mids = []
    while low <= high:
        mid = low + (high - low) // 2
        mids.append(mid)
        if mid == 3:
            break
        low = mid + 1 if mid < 3 else low
        if mid > 3:
            high = mid - 1
    assert mids == [2, 4, 3]


async def _ensure_taxonomy(db) -> None:
    for domain_data in TAXONOMY:
        if domain_data["slug"] not in {"placement", "technical"}:
            continue
        domain = (await db.execute(select(Domain).where(Domain.slug == domain_data["slug"]))).scalar_one_or_none()
        if domain is None:
            domain = Domain(name=domain_data["name"], slug=domain_data["slug"], description=domain_data["name"], is_active=True)
            db.add(domain)
            await db.flush()
        for category_data in domain_data["categories"]:
            category = (
                await db.execute(
                    select(Category).where(Category.domain_id == domain.id, Category.slug == category_data["slug"])
                )
            ).scalar_one_or_none()
            if category is None:
                category = Category(domain_id=domain.id, name=category_data["name"], slug=category_data["slug"], is_active=True)
                db.add(category)
                await db.flush()
            for topic_data in category_data["topics"]:
                topic = (
                    await db.execute(
                        select(Topic).where(Topic.category_id == category.id, Topic.slug == topic_data["slug"])
                    )
                ).scalar_one_or_none()
                if topic is None:
                    db.add(Topic(category_id=category.id, name=topic_data["name"], slug=topic_data["slug"], is_active=True))
    await ensure_dsa_taxonomy(db)
    await db.commit()


async def _laptop_question(db) -> Question:
    row = (
        await db.execute(select(Question).options(selectinload(Question.options)).where(Question.question_text == LAPTOP))
    ).scalar_one_or_none()
    if row is not None:
        return row
    topic = (
        await db.execute(
            select(Topic)
            .join(Category, Topic.category_id == Category.id)
            .join(Domain, Category.domain_id == Domain.id)
            .where(Domain.slug == "placement", Category.slug == "aptitude", Topic.slug == "percentages")
        )
    ).scalar_one()
    row = Question(
        question_type=QuestionType.SINGLE_CHOICE,
        question_text=LAPTOP,
        explanation="SHORT SEED",
        difficulty=Difficulty.EASY,
        domain_id=(await db.get(Category, topic.category_id)).domain_id,
        category_id=topic.category_id,
        topic_id=topic.id,
        marks=1.0,
        negative_marks=0.25,
        estimated_time_seconds=90,
        is_active=True,
        is_sample=True,
    )
    db.add(row)
    await db.flush()
    for index, (text, correct) in enumerate(
        [("₹34,000", True), ("₹36,000", False), ("₹32,000", False), ("₹35,000", False)]
    ):
        db.add(QuestionOption(id=uuid4(), question_id=row.id, option_text=text, is_correct=correct, sort_order=index))
    await db.commit()
    return (
        await db.execute(select(Question).options(selectinload(Question.options)).where(Question.id == row.id))
    ).scalar_one()


@pytest.mark.asyncio
async def test_sprint_batch_preserves_ids_scores_and_hides_exam_answers(client, student_auth):
    headers, email = student_auth
    async with AsyncSessionLocal() as db:
        await _ensure_taxonomy(db)
        laptop = await _laptop_question(db)
        if laptop.content_key is None:
            laptop.explanation = "SHORT SEED"
            await db.commit()
        before_id = laptop.id
        before_options = [str(opt.id) for opt in sorted(laptop.options, key=lambda item: item.sort_order)]
        before_negative = laptop.negative_marks
        user = (await db.execute(select(User).where(User.email == email))).scalar_one()
        bookmark = Bookmark(user_id=user.id, question_id=laptop.id)
        db.add(bookmark)
        await db.commit()
        bookmark_id = bookmark.id

    started = await client.post(
        "/api/v1/practice/sessions/retry",
        headers=headers,
        json={"question_ids": [str(before_id)]},
    )
    assert started.status_code == 200, started.text
    old_session = started.json()["id"]

    async with AsyncSessionLocal() as db:
        result = await apply_batch(db, BATCH, allow_remote=False)
    assert result["refused"] is False, result
    identity = {row["key"]: row for row in result["identity"]}
    laptop_row = identity["sprint1-pct-01"]
    assert laptop_row["row"] in {"adopted", "updated", "unchanged"}
    assert laptop_row["option_ids_changed"] is False
    assert laptop_row["question_id"] == str(before_id)
    assert laptop_row["option_ids"] == before_options
    created = [row for row in result["identity"] if row["row"] == "created"]
    assert created
    assert all(row["option_ids_changed"] is False and len(row["option_ids"]) == 4 for row in created)
    async with AsyncSessionLocal() as db:
        created_row = (
            await db.execute(select(Question).where(Question.content_key == created[0]["key"]))
        ).scalar_one()
        assert created_row.negative_marks == 0.25
        assert created_row.marks == 1

    hidden = await client.get(f"/api/v1/practice/sessions/{old_session}/questions/1", headers=headers)
    assert hidden.status_code == 200
    body = hidden.json()["question"]
    assert "explanation" not in body
    assert all("is_correct" not in opt for opt in body["options"])
    assert [opt["id"] for opt in body["options"]] == before_options

    submitted = await client.post(
        f"/api/v1/practice/sessions/{old_session}/questions/1/answer",
        headers=headers,
        json={"selected_option_ids": [before_options[0]], "time_spent_seconds": 3},
    )
    assert submitted.status_code == 200, submitted.text
    feedback = submitted.json()["feedback"]
    assert feedback["is_correct"] is True
    assert feedback["explanation"] == "SHORT SEED" or "SHORT SEED" in feedback["explanation"]

    fresh = await client.post(
        "/api/v1/practice/sessions/retry",
        headers=headers,
        json={"question_ids": [str(before_id)]},
    )
    assert fresh.status_code == 200, fresh.text
    fresh_id = fresh.json()["id"]
    revealed = await client.post(
        f"/api/v1/practice/sessions/{fresh_id}/questions/1/answer",
        headers=headers,
        json={"selected_option_ids": [before_options[0]], "time_spent_seconds": 2},
    )
    assert revealed.json()["feedback"]["is_correct"] is True
    assert "34,000" in revealed.json()["feedback"]["explanation"]
    assert "Step-by-step" in revealed.json()["feedback"]["explanation"]
    wrong = await client.post(
        "/api/v1/practice/sessions/retry",
        headers=headers,
        json={"question_ids": [str(before_id)]},
    )
    wrong_submit = await client.post(
        f"/api/v1/practice/sessions/{wrong.json()['id']}/questions/1/answer",
        headers=headers,
        json={"selected_option_ids": [before_options[1]], "time_spent_seconds": 2},
    )
    assert wrong_submit.json()["feedback"]["is_correct"] is False

    async with AsyncSessionLocal() as db:
        saved = (
            await db.execute(select(Question).options(selectinload(Question.options)).where(Question.id == before_id))
        ).scalar_one()
        assert saved.negative_marks == before_negative
        assert saved.topic_id == laptop.topic_id
        mark = (await db.execute(select(Bookmark).where(Bookmark.id == bookmark_id))).scalar_one()
        assert mark.question_id == before_id
        strings = (
            await db.execute(
                select(Topic)
                .join(Category, Topic.category_id == Category.id)
                .join(Domain, Category.domain_id == Domain.id)
                .where(Domain.slug == "technical", Category.slug == "dsa", Topic.slug == "strings")
            )
        ).scalar_one()
        string_topic = strings.id

    exam = await client.post(
        "/api/v1/practice/sessions",
        headers=headers,
        json={"topic_id": str(string_topic), "question_count": 2, "mode": "exam", "duration_minutes": 10},
    )
    assert exam.status_code == 200, exam.text
    exam_id = exam.json()["id"]
    exam_q = await client.get(f"/api/v1/practice/sessions/{exam_id}/questions/1", headers=headers)
    assert "explanation" not in exam_q.json()["question"]
    assert all("is_correct" not in opt for opt in exam_q.json()["question"]["options"])
    option_id = exam_q.json()["question"]["options"][0]["id"]
    exam_answer = await client.post(
        f"/api/v1/practice/sessions/{exam_id}/questions/1/answer",
        headers=headers,
        json={"selected_option_ids": [option_id], "time_spent_seconds": 1},
    )
    assert exam_answer.json()["feedback"] is None
    blocked = await client.get(f"/api/v1/practice/sessions/{exam_id}/results", headers=headers)
    assert blocked.status_code == 400
    finished = await client.post(f"/api/v1/practice/sessions/{exam_id}/complete", headers=headers)
    assert finished.status_code == 200, finished.text
    assert finished.json()["questions"][0]["explanation"]

    lesson = await client.get("/api/v1/studio/syllabus/syl-sprint-searching", headers=headers)
    assert lesson.status_code == 200, lesson.text
    practice = lesson.json()["practice"]
    assert practice
    assert all("correct" not in opt for item in practice for opt in item["options"])
    assert all("explanation" not in item for item in practice)
    checked = await client.post(
        f"/api/v1/studio/syllabus/syl-sprint-searching/practice/{practice[0]['key']}",
        headers=headers,
        json={"selected": ["0"]},
    )
    assert checked.status_code == 200, checked.text
    assert checked.json()["correct"] is True
    assert checked.json()["explanation"]
    missed = await client.post(
        f"/api/v1/studio/syllabus/syl-sprint-searching/practice/{practice[0]['key']}",
        headers=headers,
        json={"selected": ["1"]},
    )
    assert missed.json()["correct"] is False

    async with AsyncSessionLocal() as db:
        again = await apply_batch(db, BATCH, allow_remote=False)
    assert again["refused"] is False
    assert again["counts"]["question"]["unchanged"] == 70
    again_laptop = next(row for row in again["identity"] if row["key"] == "sprint1-pct-01")
    assert again_laptop["option_ids"] == before_options
    assert again_laptop["option_ids_changed"] is False
