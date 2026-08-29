import json
import uuid
from uuid import UUID

import pytest

from app.main import app
from app.services.code_execution.interface import get_code_execution_service
from app.services.code_execution.mock import MockCodeExecutionService


@pytest.fixture(autouse=True)
def mock_judge0():
    app.dependency_overrides[get_code_execution_service] = lambda: MockCodeExecutionService()
    yield
    app.dependency_overrides.pop(get_code_execution_service, None)


@pytest.fixture
async def coding_problem_id(client, admin_auth):
    response = await client.get("/api/v1/coding/problems", headers=admin_auth)
    assert response.status_code == 200, response.text
    data = response.json()
    if data["total"] == 0:
        pytest.skip("No coding problems seeded")
    return data["items"][0]["id"]


def _headers(auth_fixture):
    headers, *_ = auth_fixture
    return headers


@pytest.mark.asyncio
async def test_list_coding_problems_requires_auth(client):
    response = await client.get("/api/v1/coding/problems")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_coding_problems(client, student_auth):
    response = await client.get("/api/v1/coding/problems", headers=_headers(student_auth))
    assert response.status_code == 200
    assert "items" in response.json()


@pytest.mark.asyncio
async def test_problem_detail_hides_non_sample_tests(client, student_auth, coding_problem_id):
    detail = await client.get(
        f"/api/v1/coding/problems/{coding_problem_id}", headers=_headers(student_auth)
    )
    assert detail.status_code == 200
    body = detail.json()
    assert "sample_test_cases" in body
    for tc in body["sample_test_cases"]:
        assert tc["is_hidden"] is False if "is_hidden" in tc else True
    raw = json.dumps(body)
    assert "secret-value" not in raw


@pytest.mark.asyncio
async def test_run_public_tests_only(client, student_auth, coding_problem_id):
    run = await client.post(
        f"/api/v1/coding/problems/{coding_problem_id}/run",
        headers=_headers(student_auth),
        json={
            "source_code": "import sys\nprint(sys.stdin.read().strip())",
            "language_id": 71,
        },
    )
    assert run.status_code == 200, run.text
    body = run.json()
    assert body["submission_type"] == "run"
    for result in body["results"]:
        assert result["is_hidden"] is False
        assert result.get("input") is not None


@pytest.mark.asyncio
async def test_submit_hides_hidden_io(client, student_auth, coding_problem_id):
    submit = await client.post(
        f"/api/v1/coding/problems/{coding_problem_id}/submit",
        headers=_headers(student_auth),
        json={
            "source_code": "import sys\nprint(sys.stdin.read().strip())",
            "language_id": 71,
        },
    )
    assert submit.status_code == 200, submit.text
    body = submit.json()
    raw = json.dumps(body)
    assert "secret-value" not in raw
    hidden = [r for r in body["results"] if r["is_hidden"]]
    assert hidden
    for result in hidden:
        assert result.get("input") is None
        assert result.get("expected_output") is None
        assert result.get("stdout") is None


@pytest.mark.asyncio
async def test_submit_updates_progress(client, student_auth, coding_problem_id):
    submit = await client.post(
        f"/api/v1/coding/problems/{coding_problem_id}/submit",
        headers=_headers(student_auth),
        json={
            "source_code": "import sys\nprint(sys.stdin.read().strip())",
            "language_id": 71,
        },
    )
    assert submit.status_code == 200
    progress = await client.get("/api/v1/coding/progress", headers=_headers(student_auth))
    assert progress.status_code == 200
    summary = progress.json()
    assert summary["attempted_count"] >= 1 or summary["solved_count"] >= 1


@pytest.mark.asyncio
async def test_admin_coding_crud(client, admin_auth, student_auth):
    catalog = await client.get("/api/v1/admin/taxonomy", headers=admin_auth)
    assert catalog.status_code == 200
    domains = catalog.json()["domains"]
    technical = next(d for d in domains if d["slug"] == "technical")
    category = next(c for c in technical["categories"] if c["slug"] == "dsa")
    topic = category["topics"][0]

    slug = f"test-problem-{uuid.uuid4().hex[:8]}"
    create = await client.post(
        "/api/v1/admin/coding/problems",
        headers=admin_auth,
        json={
            "slug": slug,
            "title": "Test Problem",
            "description": "Test",
            "difficulty": "easy",
            "domain_id": technical["id"],
            "category_id": category["id"],
            "topic_id": topic["id"],
            "starter_code": {"71": "print('hi')"},
            "test_cases": [
                {
                    "name": "Public",
                    "input": "x",
                    "expected_output": "x",
                    "is_hidden": False,
                    "is_sample": True,
                },
                {
                    "name": "Hidden",
                    "input": "hidden-secret",
                    "expected_output": "hidden-secret",
                    "is_hidden": True,
                    "is_sample": False,
                },
            ],
        },
    )
    assert create.status_code == 200, create.text
    problem_id = create.json()["id"]
    assert len(create.json()["test_cases"]) == 2

    student_view = await client.get(
        f"/api/v1/coding/problems/{problem_id}", headers=_headers(student_auth)
    )
    assert student_view.status_code == 200
    assert "hidden-secret" not in json.dumps(student_view.json())

    delete = await client.delete(
        f"/api/v1/admin/coding/problems/{problem_id}", headers=admin_auth
    )
    assert delete.status_code == 200


@pytest.mark.asyncio
async def test_student_cannot_access_admin_coding(client, student_auth):
    response = await client.get("/api/v1/admin/coding/problems", headers=_headers(student_auth))
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_execution_status(client, student_auth):
    response = await client.get(
        "/api/v1/coding/execution-status", headers=_headers(student_auth)
    )
    assert response.status_code == 200
    body = response.json()
    assert "available" in body


@pytest.mark.asyncio
async def test_coding_bookmark_toggle(client, student_auth, coding_problem_id):
    headers = _headers(student_auth)
    toggle = await client.post(
        f"/api/v1/coding/problems/{coding_problem_id}/bookmark", headers=headers
    )
    assert toggle.status_code == 200
    assert toggle.json()["bookmarked"] is True

    bookmarks = await client.get("/api/v1/coding/bookmarks", headers=headers)
    assert bookmarks.status_code == 200
    ids = [item["id"] for item in bookmarks.json()]
    assert coding_problem_id in ids


@pytest.mark.asyncio
async def test_list_submissions_with_filters(client, student_auth, coding_problem_id):
    headers = _headers(student_auth)
    await client.post(
        f"/api/v1/coding/problems/{coding_problem_id}/submit",
        headers=headers,
        json={"source_code": "print('x')", "language_id": 71},
    )
    response = await client.get(
        "/api/v1/coding/submissions",
        headers=headers,
        params={"problem_id": coding_problem_id, "language_id": 71},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 1
    assert body["items"][0]["problem_id"] == coding_problem_id


@pytest.mark.asyncio
async def test_languages_endpoint(client, student_auth):
    response = await client.get("/api/v1/coding/languages", headers=_headers(student_auth))
    assert response.status_code == 200
    langs = response.json()
    assert any(lang["id"] == 71 for lang in langs)


@pytest.mark.asyncio
async def test_judge0_disabled_returns_503(client, student_auth, coding_problem_id, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "judge0_enabled", False)
    app.dependency_overrides.pop(get_code_execution_service, None)

    run = await client.post(
        f"/api/v1/coding/problems/{coding_problem_id}/run",
        headers=_headers(student_auth),
        json={"source_code": "print(1)", "language_id": 71},
    )
    assert run.status_code == 503

    app.dependency_overrides[get_code_execution_service] = lambda: MockCodeExecutionService()
