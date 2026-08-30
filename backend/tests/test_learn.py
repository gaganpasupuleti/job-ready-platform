"""Build 5: Practice Hub, courses, lessons, projects, admin gates."""

from __future__ import annotations

import pytest
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.learn import Course, PracticePath
from app.seed.learn_data import seed_learn_content


@pytest.fixture
async def learn_seed():
    await seed_learn_content()
    yield


def _headers(auth):
    return auth if isinstance(auth, dict) else auth[0]


@pytest.mark.asyncio
async def test_practice_hub_requires_auth(client):
    res = await client.get("/api/v1/practice-hub")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_practice_hub_sections(client, student_auth, learn_seed):
    headers = _headers(student_auth)
    res = await client.get("/api/v1/practice-hub", headers=headers)
    assert res.status_code == 200, res.text
    body = res.json()
    assert "sections" in body
    labels = [s["label"] for s in body["sections"]]
    assert "Programming Languages" in labels
    assert "Beginner DSA" in labels
    assert "Company Practice" in labels
    assert isinstance(body["continue_learning"], list)
    assert isinstance(body["recommended"], list)


@pytest.mark.asyncio
async def test_list_paths_and_detail(client, student_auth, learn_seed):
    headers = _headers(student_auth)
    listing = await client.get("/api/v1/paths", headers=headers)
    assert listing.status_code == 200
    paths = listing.json()
    assert any(p["slug"] == "learn-python" for p in paths)

    detail = await client.get("/api/v1/paths/learn-python", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["title"]
    assert "sections" in detail.json()


@pytest.mark.asyncio
async def test_courses_and_lesson_flow(client, student_auth, learn_seed):
    headers = _headers(student_auth)
    courses = await client.get("/api/v1/courses", headers=headers)
    assert courses.status_code == 200
    items = courses.json()
    assert any(c["slug"] == "python-foundations" for c in items)

    course = await client.get("/api/v1/courses/python-foundations", headers=headers)
    assert course.status_code == 200
    detail = course.json()
    assert detail["modules"]
    first_mod = detail["modules"][0]
    first_lesson = first_mod["lessons"][0]
    assert first_lesson["status"] != "locked"

    lesson_url = (
        f"/api/v1/courses/python-foundations/modules/{first_mod['slug']}"
        f"/lessons/{first_lesson['slug']}"
    )
    lesson = await client.get(lesson_url, headers=headers)
    assert lesson.status_code == 200, lesson.text
    body = lesson.json()
    assert body["hints"] is not None
    assert body["solution_unlocked"] is False
    assert body["solution_json"] is None
    assert body["can_mark_complete"] is True

    start = await client.post(f"/api/v1/lessons/{body['id']}/start", headers=headers)
    assert start.status_code == 200

    complete = await client.post(f"/api/v1/lessons/{body['id']}/complete", headers=headers)
    assert complete.status_code == 200, complete.text
    assert complete.json()["status"] == "completed"

    after = await client.get(lesson_url, headers=headers)
    assert after.status_code == 200
    assert after.json()["solution_unlocked"] is True
    # first concept lesson may have empty solution payload; unlock flag is what matters

    # complete second lesson that has a solution and verify payload appears
    second = first_mod["lessons"][1]
    second_url = (
        f"/api/v1/courses/python-foundations/modules/{first_mod['slug']}"
        f"/lessons/{second['slug']}"
    )
    second_detail = await client.get(second_url, headers=headers)
    assert second_detail.status_code == 200, second_detail.text
    await client.post(f"/api/v1/lessons/{second_detail.json()['id']}/complete", headers=headers)
    unlocked = await client.get(second_url, headers=headers)
    assert unlocked.json()["solution_unlocked"] is True
    assert unlocked.json()["solution_json"] is not None


@pytest.mark.asyncio
async def test_lesson_lock_previous_complete(client, student_auth, learn_seed):
    headers = _headers(student_auth)
    course = await client.get("/api/v1/courses/python-foundations", headers=headers)
    detail = course.json()
    lessons = []
    for mod in detail["modules"]:
        for lesson in mod["lessons"]:
            lessons.append((mod["slug"], lesson))

    if len(lessons) < 2:
        pytest.skip("need at least two lessons")

    second_mod, second = lessons[1]
    assert second["status"] == "locked"

    res = await client.get(
        f"/api/v1/courses/python-foundations/modules/{second_mod}/lessons/{second['slug']}",
        headers=headers,
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_unpublished_course_hidden(client, student_auth, learn_seed):
    headers = _headers(student_auth)
    async with AsyncSessionLocal() as session:
        course = (
            await session.execute(select(Course).where(Course.slug == "python-foundations"))
        ).scalar_one()
        course.is_published = False
        await session.commit()
        course_id = course.id

    try:
        listing = await client.get("/api/v1/courses", headers=headers)
        assert all(c["slug"] != "python-foundations" for c in listing.json())
        detail = await client.get("/api/v1/courses/python-foundations", headers=headers)
        assert detail.status_code in (404, 403)
    finally:
        async with AsyncSessionLocal() as session:
            course = await session.get(Course, course_id)
            course.is_published = True
            await session.commit()


@pytest.mark.asyncio
async def test_projects_list(client, student_auth, learn_seed):
    headers = _headers(student_auth)
    res = await client.get("/api/v1/projects", headers=headers)
    assert res.status_code == 200
    projects = res.json()
    assert isinstance(projects, list)
    assert any(p.get("slug") for p in projects)


@pytest.mark.asyncio
async def test_search_paths(client, student_auth, learn_seed):
    headers = _headers(student_auth)
    res = await client.get("/api/v1/practice/search", headers=headers, params={"q": "python"})
    assert res.status_code == 200
    assert "items" in res.json()


@pytest.mark.asyncio
async def test_admin_paths_forbidden_for_student(client, student_auth, learn_seed):
    headers = _headers(student_auth)
    res = await client.get("/api/v1/admin/practice-paths", headers=headers)
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_admin_paths_and_courses(client, admin_auth, learn_seed):
    res = await client.get("/api/v1/admin/practice-paths", headers=admin_auth)
    assert res.status_code == 200, res.text
    assert isinstance(res.json(), list)

    courses = await client.get("/api/v1/admin/courses", headers=admin_auth)
    assert courses.status_code == 200
    assert any(c["slug"] == "python-foundations" for c in courses.json())


@pytest.mark.asyncio
async def test_lesson_feedback(client, student_auth, learn_seed):
    headers = _headers(student_auth)
    course = await client.get("/api/v1/courses/python-foundations", headers=headers)
    mod = course.json()["modules"][0]
    lesson = mod["lessons"][0]
    detail = await client.get(
        f"/api/v1/courses/python-foundations/modules/{mod['slug']}/lessons/{lesson['slug']}",
        headers=headers,
    )
    lesson_id = detail.json()["id"]
    res = await client.post(
        f"/api/v1/lessons/{lesson_id}/feedback",
        headers=headers,
        json={"vote": "helpful", "note": "helpful"},
    )
    assert res.status_code == 200, res.text


@pytest.mark.asyncio
async def test_inactive_path_hidden(client, student_auth, learn_seed):
    headers = _headers(student_auth)
    async with AsyncSessionLocal() as session:
        path = (
            await session.execute(select(PracticePath).where(PracticePath.slug == "learn-python"))
        ).scalar_one()
        path.is_active = False
        path_id = path.id
        await session.commit()
    try:
        listing = await client.get("/api/v1/paths", headers=headers)
        assert all(p["slug"] != "learn-python" for p in listing.json())
    finally:
        async with AsyncSessionLocal() as session:
            path = await session.get(PracticePath, path_id)
            path.is_active = True
            await session.commit()
