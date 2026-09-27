"""Read-only practice tracker aggregates. Does not change Overview."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.coding import CodingProblem, CodingSubmission
from app.models.coding_enums import SubmissionStatus, SubmissionType
from app.models.enums import PracticeMode, SessionStatus
from app.models.practice import PracticeAnswer, PracticeSession, PracticeSessionQuestion
from app.models.sql_enums import SqlSubmissionStatus
from app.models.sql_practice import SqlProblem, SqlSubmission
from app.services.practice_tracker_service import utc_week_bounds


def _headers(auth):
    return auth[0] if isinstance(auth, tuple) else auth


async def _tracker(client, headers):
    response = await client.get("/api/v1/practice/tracker", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


async def _start(client, headers, *, question_count=1, mode="practice"):
    catalog = await client.get("/api/v1/practice/catalog", headers=headers)
    assert catalog.status_code == 200, catalog.text
    category = catalog.json()["domains"][0]["categories"][0]
    topic = category["topics"][0]
    created = await client.post(
        "/api/v1/practice/sessions",
        headers=headers,
        json={
            "category_id": category["id"],
            "topic_id": topic["id"],
            "question_count": question_count,
            "mode": mode,
        },
    )
    assert created.status_code == 200, created.text
    return created.json()


async def _answer_and_complete(client, headers, session_id: str):
    question = await client.get(
        f"/api/v1/practice/sessions/{session_id}/questions/1",
        headers=headers,
    )
    assert question.status_code == 200, question.text
    option_id = question.json()["question"]["options"][0]["id"]
    answered = await client.post(
        f"/api/v1/practice/sessions/{session_id}/questions/1/answer",
        headers=headers,
        json={"selected_option_ids": [option_id], "time_spent_seconds": 5},
    )
    assert answered.status_code == 200, answered.text
    completed = await client.post(
        f"/api/v1/practice/sessions/{session_id}/complete",
        headers=headers,
    )
    assert completed.status_code == 200, completed.text
    return completed.json()


async def _set_answered_at(session_id: str, moment: datetime) -> None:
    async with AsyncSessionLocal() as db:
        answers = (
            await db.execute(
                select(PracticeAnswer).where(PracticeAnswer.session_id == UUID(session_id))
            )
        ).scalars().all()
        assert answers
        for answer in answers:
            answer.answered_at = moment
        await db.commit()


@pytest.mark.asyncio
async def test_tracker_requires_auth(client):
    response = await client.get("/api/v1/practice/tracker")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_empty_account_has_no_invented_activity(client, student_auth):
    body = await _tracker(client, _headers(student_auth))
    assert body["week"]["timezone"] == "UTC"
    assert "Monday 00:00:00 UTC inclusive" in body["week"]["boundary"]
    assert body["weekly_activity"] == {
        "mcq_finalized_answers": 0,
        "coding_submits": 0,
        "sql_submits": 0,
        "total": 0,
    }
    assert body["mcq_attempted_questions"] == 0
    assert body["mcq_attempt_events"] == 0
    assert body["mcq_accuracy"]["graded_answers"] == 0
    assert body["mcq_accuracy"]["accuracy_percent"] is None
    assert body["completed_sessions"] == 0
    assert body["in_progress_sessions"] == 0
    assert body["recent_practice"] == []
    assert body["weak_topics"] == []
    assert body["recently_published"]["available"] is False
    assert "published_at" in body["recently_published"]["reason"]
    assert body["quizzes"]
    assert {item["attempt_status"] for item in body["quizzes"]} == {"not_started"}


@pytest.mark.asyncio
async def test_opening_and_active_session_are_not_completed_attempts(client, student_auth):
    headers = _headers(student_auth)
    before = await _tracker(client, headers)
    session = await _start(client, headers)
    opened = await client.get(
        f"/api/v1/practice/sessions/{session['id']}/questions/1",
        headers=headers,
    )
    assert opened.status_code == 200
    option_id = opened.json()["question"]["options"][0]["id"]
    saved = await client.post(
        f"/api/v1/practice/sessions/{session['id']}/questions/1/autosave",
        headers=headers,
        json={
            "selected_option_ids": [option_id],
            "marked_for_review": False,
            "time_spent_seconds": 3,
        },
    )
    assert saved.status_code == 200, saved.text

    active = await _tracker(client, headers)
    assert active["mcq_attempt_events"] == before["mcq_attempt_events"]
    assert active["mcq_attempted_questions"] == before["mcq_attempted_questions"]
    assert active["completed_sessions"] == before["completed_sessions"]
    assert active["in_progress_sessions"] == before["in_progress_sessions"] + 1
    assert active["mcq_accuracy"]["graded_answers"] == before["mcq_accuracy"]["graded_answers"]
    quiz = next(item for item in active["quizzes"] if item["topic_id"] == session["topic_id"])
    assert quiz["attempt_status"] == "in_progress"

    results = await _answer_and_complete(client, headers, session["id"])
    done = await _tracker(client, headers)
    assert done["completed_sessions"] == before["completed_sessions"] + 1
    assert done["in_progress_sessions"] == before["in_progress_sessions"]
    assert done["mcq_attempt_events"] == before["mcq_attempt_events"] + 1
    session_body = results["session"]
    graded = session_body["correct_count"] + session_body["incorrect_count"]
    assert done["mcq_accuracy"]["graded_answers"] == before["mcq_accuracy"]["graded_answers"] + graded
    assert done["mcq_accuracy"]["correct_answers"] == (
        before["mcq_accuracy"]["correct_answers"] + session_body["correct_count"]
    )
    if done["mcq_accuracy"]["graded_answers"]:
        expected = round(
            done["mcq_accuracy"]["correct_answers"] / done["mcq_accuracy"]["graded_answers"] * 100,
            2,
        )
        assert done["mcq_accuracy"]["accuracy_percent"] == expected
    quiz = next(item for item in done["quizzes"] if item["topic_id"] == session["topic_id"])
    assert quiz["attempt_status"] == "completed"
    assert any(item["source_id"] == session["id"] for item in done["recent_practice"])
    assert session_body["incorrect_count"] == 0 or any(
        item["topic_id"] == session["topic_id"] for item in done["weak_topics"]
    )


@pytest.mark.asyncio
async def test_tracker_is_scoped_to_the_signed_in_student(client, student_auth):
    headers = _headers(student_auth)
    session = await _start(client, headers)
    await _answer_and_complete(client, headers, session["id"])

    other = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"other_{session['id'][:8]}@example.com",
            "username": f"other_{session['id'][:8]}",
            "full_name": "Other Student",
            "password": "Student123!",
        },
    )
    assert other.status_code == 200, other.text
    other_headers = {"Authorization": f"Bearer {other.json()['access_token']}"}
    body = await _tracker(client, other_headers)
    assert body["completed_sessions"] == 0
    assert body["mcq_attempt_events"] == 0
    assert body["weekly_activity"]["total"] == 0
    assert all(item["source_id"] != session["id"] for item in body["recent_practice"])
    quiz = next(item for item in body["quizzes"] if item["topic_id"] == session["topic_id"])
    assert quiz["attempt_status"] == "not_started"


@pytest.mark.asyncio
async def test_week_boundary_uses_utc_monday_and_excludes_the_end(client, student_auth):
    headers = _headers(student_auth)
    session = await _start(client, headers)
    await _answer_and_complete(client, headers, session["id"])
    start, end = utc_week_bounds()

    await _set_answered_at(session["id"], start - timedelta(seconds=1))
    before = await _tracker(client, headers)
    assert before["weekly_activity"]["mcq_finalized_answers"] == 0
    assert before["mcq_attempt_events"] == 1

    await _set_answered_at(session["id"], start)
    inside = await _tracker(client, headers)
    assert inside["weekly_activity"]["mcq_finalized_answers"] == 1

    await _set_answered_at(session["id"], end)
    exclusive = await _tracker(client, headers)
    assert exclusive["weekly_activity"]["mcq_finalized_answers"] == 0
    assert exclusive["completed_sessions"] == 1


@pytest.mark.asyncio
async def test_repeated_attempt_counts_events_without_double_counting_the_question(
    client, student_auth
):
    headers = _headers(student_auth)
    me = await client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200, me.text
    user_id = UUID(me.json()["id"])
    session = await _start(client, headers)
    await _answer_and_complete(client, headers, session["id"])
    once = await _tracker(client, headers)

    async with AsyncSessionLocal() as db:
        original = (
            await db.execute(
                select(PracticeSession).where(PracticeSession.id == UUID(session["id"]))
            )
        ).scalar_one()
        answer = (
            await db.execute(
                select(PracticeAnswer).where(PracticeAnswer.session_id == original.id)
            )
        ).scalar_one()
        repeat = PracticeSession(
            user_id=user_id,
            mode=PracticeMode.PRACTICE,
            domain_id=original.domain_id,
            category_id=original.category_id,
            topic_id=original.topic_id,
            question_count=1,
            status=SessionStatus.COMPLETED,
            correct_count=0 if answer.is_correct else 1,
            incorrect_count=1 if answer.is_correct else 0,
            unanswered_count=0,
            score=0,
            completed_at=datetime.now(UTC),
        )
        db.add(repeat)
        await db.flush()
        db.add(
            PracticeSessionQuestion(
                session_id=repeat.id,
                question_id=answer.question_id,
                question_number=1,
            )
        )
        db.add(
            PracticeAnswer(
                session_id=repeat.id,
                question_id=answer.question_id,
                selected_option_ids=list(answer.selected_option_ids),
                is_correct=not bool(answer.is_correct),
                marks_awarded=0,
                answered_at=datetime.now(UTC),
            )
        )
        await db.commit()

    twice = await _tracker(client, headers)
    assert twice["mcq_attempt_events"] == once["mcq_attempt_events"] + 1
    assert twice["mcq_attempted_questions"] == once["mcq_attempted_questions"]
    assert twice["completed_sessions"] == once["completed_sessions"] + 1
    assert twice["mcq_accuracy"]["graded_answers"] == once["mcq_accuracy"]["graded_answers"] + 1
    assert twice["mcq_accuracy"]["accuracy_percent"] != once["mcq_accuracy"]["accuracy_percent"]


@pytest.mark.asyncio
async def test_coding_and_sql_submits_count_as_weekly_activity_not_mcq_accuracy(
    client, student_auth
):
    headers = _headers(student_auth)
    me = await client.get("/api/v1/auth/me", headers=headers)
    user_id = UUID(me.json()["id"])
    start, end = utc_week_bounds()
    before = await _tracker(client, headers)

    async with AsyncSessionLocal() as db:
        problem_id = (await db.execute(select(CodingProblem.id).limit(1))).scalar_one()
        sql_problem_id = (await db.execute(select(SqlProblem.id).limit(1))).scalar_one()
        coding = CodingSubmission(
            user_id=user_id,
            problem_id=problem_id,
            source_code="print(1)",
            language_id=71,
            language_name="Python",
            submission_type=SubmissionType.SUBMIT,
            status=SubmissionStatus.WRONG_ANSWER,
            created_at=start,
        )
        run = CodingSubmission(
            user_id=user_id,
            problem_id=problem_id,
            source_code="print(1)",
            language_id=71,
            language_name="Python",
            submission_type=SubmissionType.RUN,
            status=SubmissionStatus.ACCEPTED,
            created_at=start,
        )
        sql = SqlSubmission(
            user_id=user_id,
            problem_id=sql_problem_id,
            query_text="select 1",
            status=SqlSubmissionStatus.WRONG_ANSWER,
            submitted_at=start,
        )
        outside = SqlSubmission(
            user_id=user_id,
            problem_id=sql_problem_id,
            query_text="select 1",
            status=SqlSubmissionStatus.WRONG_ANSWER,
            submitted_at=end,
        )
        db.add_all([coding, run, sql, outside])
        await db.flush()
        coding_id = str(coding.id)
        sql_id = str(sql.id)
        await db.commit()

    body = await _tracker(client, headers)
    assert body["weekly_activity"]["coding_submits"] == before["weekly_activity"]["coding_submits"] + 1
    assert body["weekly_activity"]["sql_submits"] == before["weekly_activity"]["sql_submits"] + 1
    assert body["weekly_activity"]["mcq_finalized_answers"] == before["weekly_activity"]["mcq_finalized_answers"]
    assert body["mcq_accuracy"] == before["mcq_accuracy"]
    kinds = {(item["kind"], item["source_id"]) for item in body["recent_practice"]}
    assert ("coding_submit", str(coding_id)) in kinds
    assert ("sql_submit", str(sql_id)) in kinds
