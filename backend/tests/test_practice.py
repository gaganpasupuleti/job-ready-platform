import uuid

import pytest


@pytest.mark.asyncio
async def test_catalog_requires_auth(client):
    response = await client.get("/api/v1/practice/catalog")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_catalog_returns_domains(client, student_auth):
    headers, _ = student_auth
    response = await client.get("/api/v1/practice/catalog", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["domains"]) > 0


@pytest.mark.asyncio
async def test_create_session_and_answer(client, student_auth):
    headers, _ = student_auth
    catalog = await client.get("/api/v1/practice/catalog", headers=headers)
    aptitude = next(
        domain for domain in catalog.json()["domains"] if domain["slug"] == "placement"
    )
    category = next(cat for cat in aptitude["categories"] if cat["slug"] == "aptitude")
    topic = category["topics"][0]

    session_resp = await client.post(
        "/api/v1/practice/sessions",
        headers=headers,
        json={
            "category_id": category["id"],
            "topic_id": topic["id"],
            "difficulty": "easy",
            "question_count": 3,
            "mode": "practice",
        },
    )
    assert session_resp.status_code == 200, session_resp.text
    session_id = session_resp.json()["id"]

    question_resp = await client.get(
        f"/api/v1/practice/sessions/{session_id}/questions/1",
        headers=headers,
    )
    assert question_resp.status_code == 200
    question = question_resp.json()["question"]
    assert all("is_correct" not in option for option in question["options"])

    option_id = question["options"][0]["id"]
    answer_resp = await client.post(
        f"/api/v1/practice/sessions/{session_id}/questions/1/answer",
        headers=headers,
        json={"selected_option_ids": [option_id], "time_spent_seconds": 12},
    )
    assert answer_resp.status_code == 200
    feedback = answer_resp.json()["feedback"]
    assert feedback is not None
    assert "is_correct" in feedback

    complete_resp = await client.post(
        f"/api/v1/practice/sessions/{session_id}/complete",
        headers=headers,
    )
    assert complete_resp.status_code == 200
    assert complete_resp.json()["session"]["status"] == "completed"


@pytest.mark.asyncio
async def test_student_cannot_access_other_session(client, student_auth):
    headers, _ = student_auth
    catalog = await client.get("/api/v1/practice/catalog", headers=headers)
    category = catalog.json()["domains"][0]["categories"][0]
    topic = category["topics"][0]
    session_resp = await client.post(
        "/api/v1/practice/sessions",
        headers=headers,
        json={"category_id": category["id"], "topic_id": topic["id"], "question_count": 2},
    )
    session_id = session_resp.json()["id"]

    suffix = uuid.uuid4().hex[:8]
    other = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"other_{suffix}@example.com",
            "username": f"other_{suffix}",
            "password": "Password123!",
        },
    )
    other_headers = {"Authorization": f"Bearer {other.json()['access_token']}"}
    forbidden = await client.get(
        f"/api/v1/practice/sessions/{session_id}",
        headers=other_headers,
    )
    assert forbidden.status_code == 404


@pytest.mark.asyncio
async def test_admin_questions_requires_admin(client, student_auth):
    headers, _ = student_auth
    response = await client.get("/api/v1/admin/questions", headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_list_questions(client, admin_auth):
    response = await client.get("/api/v1/admin/questions", headers=admin_auth)
    assert response.status_code == 200
    assert response.json()["total"] >= 1
