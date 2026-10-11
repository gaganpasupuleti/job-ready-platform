"""Session integrity: persisted option presentation order and the results reveal policy."""

import random
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.enums import QuestionType
from app.models.practice import PracticeSessionQuestion
from app.models.question import QuestionOption
from app.services import practice_service
from app.services.practice_service import PracticeService, question_snapshot, view_question


def _fake_question(
    correct_positions: set[int],
    question_type=QuestionType.SINGLE_CHOICE,
    *,
    title=None,
    content_key=None,
):
    return SimpleNamespace(
        id=uuid4(),
        content_key=content_key,
        question_type=question_type,
        title=title,
        question_text="Which option is right?",
        explanation="Because.",
        difficulty="easy",
        marks=1.0,
        negative_marks=0.25,
        estimated_time_seconds=60,
        topic_id=None,
        options=[
            SimpleNamespace(
                id=uuid4(),
                option_text=f"Option {i}",
                is_correct=i in correct_positions,
                sort_order=i,
            )
            for i in range(4)
        ],
    )


def test_correct_option_reaches_every_display_position(monkeypatch):
    question = _fake_question({0})
    canonical = {(str(o.id), o.option_text, o.is_correct, o.sort_order) for o in question.options}
    positions = set()
    for seed in range(20):
        monkeypatch.setattr(practice_service, "_presentation_rng", random.Random(seed))
        options = question_snapshot(question)["options"]
        assert {
            (o["id"], o["option_text"], o["is_correct"], o["sort_order"]) for o in options
        } == canonical
        positions.add(next(i for i, o in enumerate(options) if o["is_correct"]))
    assert positions == {0, 1, 2, 3}


def test_multi_select_scoring_is_independent_of_presentation(monkeypatch):
    question = _fake_question({0, 1}, QuestionType.MULTIPLE_CHOICE)
    correct_ids = [o.id for o in question.options if o.is_correct]
    service = PracticeService(None)
    for seed in range(5):
        monkeypatch.setattr(practice_service, "_presentation_rng", random.Random(seed))
        view = view_question(question, question_snapshot(question))
        assert service._evaluate_answer(view, correct_ids) == (True, 1.0)
        assert service._evaluate_answer(view, correct_ids[:1]) == (False, -0.25)


def test_internal_content_key_is_not_shown_as_a_title():
    service = PracticeService(None)
    keyed = _fake_question({0}, title="sat-quant-01", content_key="sat-quant-01")
    named = _fake_question({0}, title="Train crossing a platform", content_key="sat-quant-02")
    for question in (keyed, named):
        live = service._public_question(question, None, [])
        snap = service._public_question(
            view_question(question, question_snapshot(question)), None, []
        )
        expected = None if question is keyed else "Train crossing a platform"
        assert live.title == expected
        assert snap.title == expected


async def _start(client, headers, *, mode="practice", question_count=3):
    catalog = await client.get("/api/v1/practice/catalog", headers=headers)
    category = catalog.json()["domains"][0]["categories"][0]
    topic = category["topics"][0]
    resp = await client.post(
        "/api/v1/practice/sessions",
        headers=headers,
        json={
            "category_id": category["id"],
            "topic_id": topic["id"],
            "question_count": question_count,
            "mode": mode,
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["id"]


async def _session_questions(session_id: str) -> list[PracticeSessionQuestion]:
    async with AsyncSessionLocal() as db:
        rows = await db.execute(
            select(PracticeSessionQuestion)
            .where(PracticeSessionQuestion.session_id == UUID(session_id))
            .order_by(PracticeSessionQuestion.question_number)
        )
        return list(rows.scalars())


async def _correct_option_ids(question_id: UUID) -> set[str]:
    async with AsyncSessionLocal() as db:
        rows = await db.execute(
            select(QuestionOption.id).where(
                QuestionOption.question_id == question_id, QuestionOption.is_correct.is_(True)
            )
        )
        return {str(value) for value in rows.scalars()}


@pytest.mark.asyncio
async def test_presentation_order_is_persisted_and_scoring_uses_ids(
    client, student_auth, monkeypatch
):
    headers, _ = student_auth
    monkeypatch.setattr(practice_service, "_presentation_rng", random.Random(7))
    session_id = await _start(client, headers)

    first = await client.get(f"/api/v1/practice/sessions/{session_id}/questions/1", headers=headers)
    again = await client.get(f"/api/v1/practice/sessions/{session_id}/questions/1", headers=headers)
    shown = first.json()["question"]["options"]
    assert [o["id"] for o in shown] == [o["id"] for o in again.json()["question"]["options"]]
    assert [o["sort_order"] for o in shown] == list(range(len(shown)))

    rows = await _session_questions(session_id)
    assert [o["id"] for o in rows[0].snapshot_json["options"]] == [o["id"] for o in shown]

    correct = await _correct_option_ids(rows[0].question_id)
    answer = await client.post(
        f"/api/v1/practice/sessions/{session_id}/questions/1/answer",
        headers=headers,
        json={"selected_option_ids": sorted(correct), "time_spent_seconds": 5},
    )
    assert answer.status_code == 200, answer.text
    feedback = answer.json()["feedback"]
    assert feedback["is_correct"] is True
    assert set(feedback["correct_option_ids"]) == correct
    assert [o["id"] for o in feedback["options"]] == [o["id"] for o in shown]


@pytest.mark.asyncio
async def test_existing_snapshot_order_is_never_reshuffled(client, student_auth):
    headers, _ = student_auth
    session_id = await _start(client, headers, question_count=1)
    rows = await _session_questions(session_id)
    canonical = sorted(rows[0].snapshot_json["options"], key=lambda o: o["sort_order"])

    async with AsyncSessionLocal() as db:
        row = await db.get(PracticeSessionQuestion, rows[0].id)
        row.snapshot_json = {**row.snapshot_json, "options": canonical}
        await db.commit()

    for _ in range(3):
        resp = await client.get(
            f"/api/v1/practice/sessions/{session_id}/questions/1", headers=headers
        )
        assert [o["id"] for o in resp.json()["question"]["options"]] == [o["id"] for o in canonical]


@pytest.mark.asyncio
async def test_active_practice_results_withhold_unanswered_questions(client, student_auth):
    headers, _ = student_auth
    session_id = await _start(client, headers, question_count=2)
    q1 = await client.get(f"/api/v1/practice/sessions/{session_id}/questions/1", headers=headers)
    option_id = q1.json()["question"]["options"][0]["id"]
    answered = await client.post(
        f"/api/v1/practice/sessions/{session_id}/questions/1/answer",
        headers=headers,
        json={"selected_option_ids": [option_id], "time_spent_seconds": 3},
    )
    assert answered.status_code == 200, answered.text

    autosaved = await client.post(
        f"/api/v1/practice/sessions/{session_id}/questions/2/autosave",
        headers=headers,
        json={"selected_option_ids": [], "marked_for_review": True, "time_spent_seconds": 1},
    )
    assert autosaved.status_code == 200, autosaved.text

    active = await client.get(f"/api/v1/practice/sessions/{session_id}/results", headers=headers)
    assert active.status_code == 200, active.text
    first, second = active.json()["questions"]
    assert first["correct_option_ids"]
    assert first["correct_option_texts"]
    assert second["correct_option_ids"] == []
    assert second["correct_option_texts"] == []
    assert second["explanation"] is None

    completed = await client.post(
        f"/api/v1/practice/sessions/{session_id}/complete", headers=headers
    )
    assert completed.status_code == 200, completed.text
    assert all(item["correct_option_ids"] for item in completed.json()["questions"])


@pytest.mark.asyncio
async def test_results_are_private_to_the_session_owner(client, student_auth):
    headers, _ = student_auth
    session_id = await _start(client, headers, question_count=1)
    suffix = uuid4().hex[:8]
    other = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"other_{suffix}@example.com",
            "username": f"other_{suffix}",
            "password": "Password123!",
        },
    )
    other_headers = {"Authorization": f"Bearer {other.json()['access_token']}"}
    resp = await client.get(
        f"/api/v1/practice/sessions/{session_id}/results", headers=other_headers
    )
    assert resp.status_code == 404
