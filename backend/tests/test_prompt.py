"""Build 6: AI taxonomy, prompt challenges, deterministic evaluators."""

from __future__ import annotations

import pytest
from sqlalchemy import select

from app.content.validator import validate_file_payload
from app.db.session import AsyncSessionLocal
from app.models.prompt import PromptChallenge
from app.seed.build6_seed import seed_build6_content
from app.services.prompt_evaluator import PromptEvaluator, run_check, validate_challenge_config


def _h(auth):
    return auth if isinstance(auth, dict) else auth[0]


@pytest.fixture
async def ai_seed():
    await seed_build6_content()
    yield


@pytest.mark.asyncio
async def test_ai_taxonomy_in_catalog(client, student_auth, ai_seed):
    res = await client.get("/api/v1/practice/catalog", headers=_h(student_auth))
    assert res.status_code == 200
    domains = {d["slug"]: d for d in res.json()["domains"]}
    assert "ai" in domains
    topics = [t["slug"] for c in domains["ai"]["categories"] for t in c["topics"]]
    for needed in ("llm-fundamentals", "rag", "mcp-fundamentals", "ai-security", "transformers"):
        assert needed in topics


@pytest.mark.asyncio
async def test_prompt_challenge_list_and_detail_hides_hidden(client, student_auth, ai_seed):
    headers = _h(student_auth)
    listing = await client.get("/api/v1/ai/prompts", headers=headers)
    assert listing.status_code == 200
    items = listing.json()
    assert len(items) >= 25
    slug = "support-ticket-classifier"
    detail = await client.get(f"/api/v1/ai/prompts/{slug}", headers=headers)
    assert detail.status_code == 200
    body = detail.json()
    assert body["hidden_case_count"] >= 1
    blob = str(body)
    assert "HIDDEN_SAMPLE" not in blob
    for case in body["public_cases"]:
        assert case["is_hidden"] is False


@pytest.mark.asyncio
async def test_unpublished_prompt_hidden(client, student_auth, admin_auth, ai_seed):
    async with AsyncSessionLocal() as session:
        row = (
            await session.execute(select(PromptChallenge).where(PromptChallenge.slug == "support-ticket-classifier"))
        ).scalar_one()
        row.is_active = False
        await session.commit()
        cid = str(row.id)
    res = await client.get("/api/v1/ai/prompts/support-ticket-classifier", headers=_h(student_auth))
    assert res.status_code == 404
    await client.patch(f"/api/v1/admin/ai/prompts/{cid}", headers=admin_auth, json={"is_active": True})


@pytest.mark.asyncio
async def test_test_vs_submit_and_mastery(client, student_auth, ai_seed):
    headers = _h(student_auth)
    slug = "support-ticket-classifier"
    detail = await client.get(f"/api/v1/ai/prompts/{slug}", headers=headers)
    starter = detail.json()["starter_prompt"]
    tested = await client.post(f"/api/v1/ai/prompts/{slug}/test", headers=headers, json={"prompt_text": starter})
    assert tested.status_code == 200, tested.text
    tbody = tested.json()
    assert tbody["is_test"] is True
    assert tbody["total_cases"] == len(detail.json()["public_cases"])
    submitted = await client.post(f"/api/v1/ai/prompts/{slug}/submit", headers=headers, json={"prompt_text": starter})
    assert submitted.status_code == 200, submitted.text
    sbody = submitted.json()
    assert sbody["is_test"] is False
    assert sbody["total_cases"] > tbody["total_cases"]
    assert sbody["overall_score"] >= 80
    assert sbody["mastered"] is True
    for row in sbody["case_results"]:
        if not row["revealed"]:
            assert row["check_results"] == []
            assert "HIDDEN" not in row["feedback"]


@pytest.mark.asyncio
async def test_prompt_submissions_ownership(client, student_auth, ai_seed):
    headers = _h(student_auth)
    slug = "sentiment-classification"
    detail = await client.get(f"/api/v1/ai/prompts/{slug}", headers=headers)
    sub = await client.post(
        f"/api/v1/ai/prompts/{slug}/submit",
        headers=headers,
        json={"prompt_text": detail.json()["starter_prompt"]},
    )
    sid = sub.json()["submission_id"]
    mine = await client.get(f"/api/v1/ai/prompt-submissions/{sid}", headers=headers)
    assert mine.status_code == 200
    listed = await client.get("/api/v1/ai/prompt-submissions", headers=headers)
    assert any(item["id"] == sid for item in listed.json())

    other = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"other_prompt_{sid[:8]}@example.com",
            "username": f"op{sid[:8]}",
            "full_name": "Other",
            "password": "Student123!",
        },
    )
    token = other.json()["access_token"]
    forbidden = await client.get(
        f"/api/v1/ai/prompt-submissions/{sid}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert forbidden.status_code == 403


@pytest.mark.asyncio
async def test_prompt_bookmarks(client, student_auth, ai_seed):
    headers = _h(student_auth)
    listing = await client.get("/api/v1/ai/prompts", headers=headers)
    cid = listing.json()[0]["id"]
    tog = await client.post(f"/api/v1/ai/prompts/{cid}/bookmark", headers=headers)
    assert tog.json()["bookmarked"] is True
    marks = await client.get("/api/v1/ai/prompt-bookmarks", headers=headers)
    assert any(m["id"] == cid for m in marks.json())


@pytest.mark.asyncio
async def test_ai_progress_and_home(client, student_auth, ai_seed):
    headers = _h(student_auth)
    home = await client.get("/api/v1/ai/home", headers=headers)
    assert home.status_code == 200
    assert home.json()["tracks"]
    prog = await client.get("/api/v1/ai/progress", headers=headers)
    assert prog.status_code == 200
    keys = {t["key"] for t in prog.json()["topics"]}
    assert {"genai", "rag", "prompt", "agents", "mcp", "security"} <= keys


@pytest.mark.asyncio
async def test_admin_ai_permissions(client, student_auth, admin_auth, ai_seed):
    denied = await client.get("/api/v1/admin/ai", headers=_h(student_auth))
    assert denied.status_code == 403
    ok = await client.get("/api/v1/admin/ai", headers=admin_auth)
    assert ok.status_code == 200
    assert ok.json()["ai_mcqs"] >= 80
    prompts = await client.get("/api/v1/admin/ai/prompts", headers=admin_auth)
    assert len(prompts.json()) >= 25
    cid = prompts.json()[0]["id"]
    val = await client.post(f"/api/v1/admin/ai/prompts/{cid}/validate", headers=admin_auth)
    assert val.status_code == 200
    assert val.json()["ok"] is True


@pytest.mark.asyncio
async def test_admin_cannot_activate_invalid(client, admin_auth, ai_seed):
    payload = {
        "slug": "invalid-no-public-cases",
        "title": "Invalid",
        "task_type": "classification",
        "difficulty": "easy",
        "is_active": True,
        "cases": [
            {
                "is_hidden": True,
                "evaluation_config": {"checks": [{"type": "contains", "value": "x"}]},
            }
        ],
    }
    res = await client.post("/api/v1/admin/ai/prompts", headers=admin_auth, json=payload)
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_ai_practice_paths(client, student_auth, ai_seed):
    res = await client.get("/api/v1/paths", headers=_h(student_auth))
    slugs = {p["slug"] for p in res.json()}
    assert "ai-rag" in slugs
    assert "ai-mcp" in slugs


def test_evaluators_unit():
    ev = PromptEvaluator()
    prompt = 'Output JSON {"category":"billing","priority":"low"} and use {{ticket_text}}'
    rendered = prompt.replace("{{ticket_text}}", "hello")
    assert run_check({"type": "exact_match", "value": "abc"}, prompt="abc", rendered="abc", variables={})[0]
    assert run_check({"type": "contains", "value": "JSON"}, prompt=prompt, rendered=rendered, variables={})[0]
    assert run_check({"type": "regex", "pattern": r"category"}, prompt=prompt, rendered=rendered, variables={})[0]
    assert run_check({"type": "json_validity"}, prompt=prompt, rendered=rendered, variables={})[0]
    schema = {
        "type": "object",
        "required": ["category"],
        "additionalProperties": True,
        "properties": {"category": {"type": "string", "enum": ["billing"]}},
    }
    assert run_check({"type": "json_schema", "schema": schema}, prompt=prompt, rendered=rendered, variables={})[0]
    assert run_check(
        {"type": "classification_label", "labels": ["billing"]}, prompt=prompt, rendered=rendered, variables={}
    )[0]
    assert run_check({"type": "variable_used", "names": ["ticket_text"]}, prompt=prompt, rendered=rendered, variables={})[0]
    row = ev.evaluate_case(
        prompt=prompt,
        case_variables={"ticket_text": "x"},
        evaluation_config={"checks": [{"type": "contains", "value": "JSON"}]},
    )
    assert row["passed"] is True
    overall, breakdown, _ = ev.aggregate([{"score": 100, "weight": 1, "check_results": []}], {"task_accuracy": 1})
    assert 0 <= overall <= 100
    assert "task_accuracy" in breakdown
    errors = validate_challenge_config({}, [])
    assert any("public case" in e.lower() for e in errors)


@pytest.mark.asyncio
async def test_content_factory_prompt_schema():
    async with AsyncSessionLocal() as session:
        results, items = await validate_file_payload(
            session,
            {
                "content_kind": "prompt_challenge",
                "prompt_challenges": [
                    {
                        "slug": "factory-prompt",
                        "title": "Factory prompt",
                        "task_type": "classification",
                        "difficulty": "easy",
                        "cases": [
                            {
                                "evaluation_config": {"checks": [{"type": "contains", "value": "json"}]},
                                "is_hidden": False,
                            }
                        ],
                    }
                ],
            },
        )
    assert items
    assert not results[0].errors
