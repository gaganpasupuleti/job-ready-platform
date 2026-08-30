"""Build 7.1: workspace navigation, path idempotency, project task sync."""

from __future__ import annotations

import pytest
from app.seed.learn_data import seed_learn_content


@pytest.fixture
async def learn_seed():
    await seed_learn_content()
    yield


def _h(auth):
    return auth if isinstance(auth, dict) else auth[0]


@pytest.mark.asyncio
async def test_path_item_completion_is_idempotent(client, student_auth, learn_seed):
    headers = _h(student_auth)
    detail = await client.get("/api/v1/paths/beginner-arrays", headers=headers)
    assert detail.status_code == 200, detail.text
    body = detail.json()
    path_id = body["id"]
    item = next(i for s in body["sections"] for i in s["items"])
    first = await client.post(f"/api/v1/paths/{path_id}/items/{item['id']}/complete", headers=headers)
    assert first.status_code == 200, first.text
    percent = first.json()["percent"]
    second = await client.post(f"/api/v1/paths/{path_id}/items/{item['id']}/complete", headers=headers)
    assert second.status_code == 200
    assert second.json()["percent"] == percent
    assert second.json().get("already_completed") is True
    again = await client.get("/api/v1/paths/beginner-arrays", headers=headers)
    completed = [i for s in again.json()["sections"] for i in s["items"] if i["id"] == item["id"]]
    assert completed[0]["completed"] is True


@pytest.mark.asyncio
async def test_sql_navigation_endpoint(client, student_auth):
    headers = _h(student_auth)
    listing = await client.get("/api/v1/sql/problems?limit=5", headers=headers)
    if listing.status_code != 200 or not listing.json().get("items"):
        pytest.skip("SQL problems not seeded")
    slug = listing.json()["items"][0]["slug"]
    nav = await client.get(f"/api/v1/sql/problems/{slug}/navigation", headers=headers)
    assert nav.status_code == 200, nav.text
    body = nav.json()
    assert body["position"] >= 1
    assert body["total"] >= 1
    assert body["items"]


@pytest.mark.asyncio
async def test_coding_navigation_and_hidden_solution(client, student_auth):
    headers = _h(student_auth)
    listing = await client.get("/api/v1/coding/problems?limit=5", headers=headers)
    if listing.status_code != 200 or not listing.json().get("items"):
        pytest.skip("Coding problems not seeded")
    problem_id = listing.json()["items"][0]["id"]
    nav = await client.get(f"/api/v1/coding/problems/{problem_id}/navigation", headers=headers)
    assert nav.status_code == 200, nav.text
    detail = await client.get(f"/api/v1/coding/problems/{problem_id}", headers=headers)
    assert detail.status_code == 200
    body = detail.json()
    assert body.get("solution") in (None, {})
    assert body.get("solution_unlocked") in (False, None)


@pytest.mark.asyncio
async def test_project_task_workspace_and_checklist(client, student_auth, learn_seed):
    headers = _h(student_auth)
    detail = await client.get("/api/v1/projects/python-calculator", headers=headers)
    assert detail.status_code == 200
    project = detail.json()
    task = project["modules"][0]["tasks"][0]
    page = await client.get(f"/api/v1/projects/python-calculator/tasks/{task['id']}", headers=headers)
    assert page.status_code == 200, page.text
    assert page.json()["task"]["id"] == task["id"]
    assert page.json()["task"]["workspace_href"].endswith(f"/tasks/{task['id']}")

    if task.get("checklist_json"):
        patch = await client.patch(
            f"/api/v1/projects/{project['id']}/tasks/{task['id']}/checklist",
            headers=headers,
            json={"checked": {"0": True}},
        )
        assert patch.status_code == 200, patch.text


@pytest.mark.asyncio
async def test_project_linked_sql_completion(client, student_auth, learn_seed):
    headers = _h(student_auth)
    detail = await client.get("/api/v1/projects/sql-ecommerce-analytics", headers=headers)
    assert detail.status_code == 200
    tasks = [t for m in detail.json()["modules"] for t in m["tasks"]]
    sql_task = next((t for t in tasks if t.get("sql_problem_id") or (t.get("engine_href") or "").startswith("/practice/sql")), None)
    if sql_task is None:
        pytest.skip("No linked SQL project task")
    assert (sql_task.get("engine_href") or "").startswith("/practice/sql") or (sql_task.get("href") or "").startswith(
        "/projects/"
    )


@pytest.mark.asyncio
async def test_workspace_navigation_metadata_on_path_items(client, student_auth, learn_seed):
    headers = _h(student_auth)
    detail = await client.get("/api/v1/paths/beginner-arrays", headers=headers)
    items = [i for s in detail.json()["sections"] for i in s["items"]]
    assert items
    assert "completed" in items[0]
