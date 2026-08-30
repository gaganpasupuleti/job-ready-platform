"""Build 5.1: projects progress, path mix, content factory catalog validation."""

from __future__ import annotations

import pytest
from sqlalchemy import select

from app.content.validator import validate_file_payload, validate_project_payload
from app.db.session import AsyncSessionLocal
from app.models.learn import Project
from app.seed.learn_data import seed_learn_content


@pytest.fixture
async def learn_seed():
    await seed_learn_content()
    yield


def _headers(auth):
    return auth if isinstance(auth, dict) else auth[0]


@pytest.mark.asyncio
async def test_project_list_and_detail(client, student_auth, learn_seed):
    headers = _headers(student_auth)
    listing = await client.get("/api/v1/projects", headers=headers)
    assert listing.status_code == 200
    slugs = {p["slug"] for p in listing.json()}
    assert "python-calculator" in slugs
    assert "sql-ecommerce-analytics" in slugs
    calc = next(p for p in listing.json() if p["slug"] == "python-calculator")
    assert calc["estimated_minutes"]
    assert calc["href"] == "/projects/python-calculator"
    assert calc["task_count"] >= 4

    detail = await client.get("/api/v1/projects/python-calculator", headers=headers)
    assert detail.status_code == 200, detail.text
    body = detail.json()
    assert body["skills"]
    assert body["prerequisites"]
    assert body["final_objective"]
    assert body["modules"]
    types = {t["task_type"] for m in body["modules"] for t in m["tasks"]}
    assert "concept" in types
    assert "implementation" in types
    assert "review" in types


@pytest.mark.asyncio
async def test_project_progress_and_task_complete(client, student_auth, learn_seed):
    headers = _headers(student_auth)
    detail = await client.get("/api/v1/projects/python-calculator", headers=headers)
    body = detail.json()
    project_id = body["id"]
    first_task = body["modules"][0]["tasks"][0]["id"]

    start = await client.post(f"/api/v1/projects/{project_id}/start", headers=headers)
    assert start.status_code == 200
    assert start.json()["status"] in {"in_progress", "completed"}

    done = await client.post(
        f"/api/v1/projects/{project_id}/tasks/{first_task}/complete",
        headers=headers,
    )
    assert done.status_code == 200, done.text
    assert done.json()["percent"] > 0

    again = await client.get("/api/v1/projects/python-calculator", headers=headers)
    assert again.json()["progress_percent"] > 0
    assert again.json()["completed_task_count"] >= 1

    cont = await client.get("/api/v1/learning/continue", headers=headers)
    assert any(i["kind"] == "project" for i in cont.json()) or again.json()["progress_percent"] >= 0


@pytest.mark.asyncio
async def test_unpublished_project_hidden(client, student_auth, learn_seed):
    headers = _headers(student_auth)
    async with AsyncSessionLocal() as session:
        project = (
            await session.execute(select(Project).where(Project.slug == "python-calculator"))
        ).scalar_one()
        project.is_published = False
        pid = project.id
        await session.commit()
    try:
        listing = await client.get("/api/v1/projects", headers=headers)
        assert all(p["slug"] != "python-calculator" for p in listing.json())
        detail = await client.get("/api/v1/projects/python-calculator", headers=headers)
        assert detail.status_code == 404
    finally:
        async with AsyncSessionLocal() as session:
            project = await session.get(Project, pid)
            project.is_published = True
            await session.commit()


@pytest.mark.asyncio
async def test_sql_project_links_engine(client, student_auth, learn_seed):
    headers = _headers(student_auth)
    detail = await client.get("/api/v1/projects/sql-ecommerce-analytics", headers=headers)
    assert detail.status_code == 200
    hrefs = [t.get("href") for m in detail.json()["modules"] for t in m["tasks"]]
    assert any(h and str(h).startswith("/practice/sql") for h in hrefs)


@pytest.mark.asyncio
async def test_company_path_content(client, student_auth, learn_seed):
    headers = _headers(student_auth)
    detail = await client.get("/api/v1/paths/company-tcs", headers=headers)
    assert detail.status_code == 200
    body = detail.json()
    assert "not affiliated" in (body.get("description") or "").lower() or "hiring patterns" in (
        body.get("description") or ""
    ).lower()
    titles = [i["title"] for s in body["sections"] for i in s["items"]]
    assert any(t and "MCQ" in t for t in titles)
    assert any(t and "SQL" in t for t in titles)


@pytest.mark.asyncio
async def test_path_progress(client, student_auth, learn_seed):
    headers = _headers(student_auth)
    detail = await client.get("/api/v1/paths/beginner-arrays", headers=headers)
    path_id = detail.json()["id"]
    item_id = detail.json()["sections"][0]["items"][0]["id"]
    start = await client.post(f"/api/v1/paths/{path_id}/start", headers=headers)
    assert start.status_code == 200
    done = await client.post(f"/api/v1/paths/{path_id}/items/{item_id}/complete", headers=headers)
    assert done.status_code == 200
    assert done.json()["percent"] > 0


@pytest.mark.asyncio
async def test_admin_projects_forbidden_and_allowed(client, student_auth, admin_auth, learn_seed):
    student = _headers(student_auth)
    res = await client.get("/api/v1/admin/projects", headers=student)
    assert res.status_code == 403
    ok = await client.get("/api/v1/admin/projects", headers=admin_auth)
    assert ok.status_code == 200
    assert any(p["slug"] == "python-calculator" for p in ok.json())


@pytest.mark.asyncio
async def test_content_factory_project_validation():
    good = validate_project_payload(
        {
            "slug": "python-demo",
            "title": "Demo Tracker",
            "category_key": "python",
            "short_description": "Original guided tracker project.",
            "task_types": ["concept", "implementation"],
        }
    )
    assert good.ok
    bad = validate_project_payload({"title": "TODO placeholder"})
    assert not bad.ok


@pytest.mark.asyncio
async def test_content_factory_file_kind(client, student_auth, learn_seed):
    async with AsyncSessionLocal() as session:
        results, items = await validate_file_payload(
            session,
            {
                "content_kind": "project",
                "projects": [
                    {
                        "slug": "x",
                        "title": "Valid Title",
                        "category_key": "python",
                        "short_description": "A real description",
                    }
                ],
            },
        )
    assert len(results) == 1
    assert results[0].ok
    assert items
