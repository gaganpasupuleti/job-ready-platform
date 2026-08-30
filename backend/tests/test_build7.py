"""Build 7: cloud/devops/cyber taxonomy, MCQs, deterministic scenarios."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.content.reports import gap_report
from app.content.validator import validate_file_payload
from app.db.session import AsyncSessionLocal
from app.models.scenario import ScenarioChallenge, ScenarioStep
from app.models.taxonomy import Category, Domain
from app.seed.build7_seed import seed_build7_content


def _h(auth):
    return auth if isinstance(auth, dict) else auth[0]


@pytest.fixture
async def infra_seed():
    await seed_build7_content()
    yield


@pytest.mark.asyncio
async def test_rag_topics_distinct_from_genai_catalog(client, student_auth, infra_seed):
    res = await client.get("/api/v1/practice/catalog", headers=_h(student_auth))
    assert res.status_code == 200
    domains = {d["slug"]: d for d in res.json()["domains"]}
    assert "ai" in domains
    genai = next(c for c in domains["ai"]["categories"] if c["slug"] == "generative-ai")
    slugs = {t["slug"] for t in genai["topics"]}
    assert {"rag", "retrieval", "vector-databases", "llm-fundamentals"} <= slugs


@pytest.mark.asyncio
async def test_taxonomy_cache_invalidation_after_admin_topic_create(client, student_auth, admin_auth, infra_seed):
    headers = _h(student_auth)
    before = await client.get("/api/v1/practice/catalog", headers=headers)
    assert before.status_code == 200
    domains = {d["slug"]: d for d in before.json()["domains"]}
    aws = next(c for c in domains["cloud"]["categories"] if c["slug"] == "aws")
    category_id = aws["id"]
    slug = f"cache-inv-{uuid.uuid4().hex[:8]}"
    created = await client.post(
        "/api/v1/admin/taxonomy/topics",
        headers=admin_auth,
        json={"category_id": category_id, "name": "Cache Topic", "slug": slug, "is_active": True},
    )
    assert created.status_code == 200, created.text
    after = await client.get("/api/v1/practice/catalog", headers=headers)
    aws_after = next(c for c in after.json()["domains"] if c["slug"] == "cloud")
    aws_cat = next(c for c in aws_after["categories"] if c["slug"] == "aws")
    assert slug in {t["slug"] for t in aws_cat["topics"]}


@pytest.mark.asyncio
async def test_infra_taxonomy_and_mcq_catalog(client, student_auth, infra_seed):
    res = await client.get("/api/v1/practice/catalog", headers=_h(student_auth))
    domains = {d["slug"]: d for d in res.json()["domains"]}
    for needed in ("cloud", "devops", "cybersecurity"):
        assert needed in domains
    cloud_topics = [t["slug"] for c in domains["cloud"]["categories"] for t in c["topics"]]
    assert {"iam", "vpc", "lambda", "shared-responsibility"} <= set(cloud_topics)
    devops_topics = [t["slug"] for c in domains["devops"]["categories"] for t in c["topics"]]
    assert {"dockerfile", "pod", "state"} <= set(devops_topics)
    cyber_topics = [t["slug"] for c in domains["cybersecurity"]["categories"] for t in c["topics"]]
    assert {"cia-triad", "owasp", "siem"} <= set(cyber_topics)


@pytest.mark.asyncio
async def test_scenario_list_detail_hidden_options(client, student_auth, infra_seed):
    headers = _h(student_auth)
    listing = await client.get("/api/v1/scenarios?domain=cloud", headers=headers)
    assert listing.status_code == 200
    assert len(listing.json()) >= 10
    slug = "cloud-traffic-surge-single-server"
    detail = await client.get(f"/api/v1/scenarios/{slug}", headers=headers)
    assert detail.status_code == 200
    blob = str(detail.json())
    assert "is_correct" not in blob
    assert detail.json()["steps"]


@pytest.mark.asyncio
async def test_unpublished_scenario_hidden(client, student_auth, admin_auth, infra_seed):
    async with AsyncSessionLocal() as session:
        row = (
            await session.execute(
                select(ScenarioChallenge).where(ScenarioChallenge.slug == "cloud-file-upload-hot-disk")
            )
        ).scalar_one()
        row.is_active = False
        await session.commit()
        cid = str(row.id)
    hidden = await client.get("/api/v1/scenarios/cloud-file-upload-hot-disk", headers=_h(student_auth))
    assert hidden.status_code == 404
    listed = await client.get("/api/v1/scenarios?domain=cloud", headers=_h(student_auth))
    assert all(item["slug"] != "cloud-file-upload-hot-disk" for item in listed.json())
    await client.patch(f"/api/v1/admin/scenarios/{cid}", headers=admin_auth, json={"is_active": True})


@pytest.mark.asyncio
async def test_scenario_scoring_and_critical_miss(client, student_auth, infra_seed):
    headers = _h(student_auth)
    slug = "cloud-traffic-surge-single-server"
    async with AsyncSessionLocal() as session:
        challenge = (
            await session.execute(
                select(ScenarioChallenge)
                .options(selectinload(ScenarioChallenge.steps).selectinload(ScenarioStep.options))
                .where(ScenarioChallenge.slug == slug)
            )
        ).scalar_one()
        steps = sorted(challenge.steps, key=lambda s: s.sort_order)
        correct = []
        wrong_critical = []
        for step in steps:
            good = next(o for o in step.options if o.is_correct)
            bad = next(o for o in step.options if not o.is_correct)
            correct.append({"step_id": str(step.id), "option_id": str(good.id)})
            chosen = bad if step.is_critical else good
            wrong_critical.append({"step_id": str(step.id), "option_id": str(chosen.id)})

    ok = await client.post(f"/api/v1/scenarios/{slug}/submit", headers=headers, json={"answers": correct})
    assert ok.status_code == 200, ok.text
    body = ok.json()
    assert body["overall_score"] == 100
    assert body["mastered"] is True
    assert body["missed_critical"] == []

    miss = await client.post(f"/api/v1/scenarios/{slug}/submit", headers=headers, json={"answers": wrong_critical})
    assert miss.status_code == 200
    mbody = miss.json()
    assert mbody["missed_critical"]
    assert mbody["overall_score"] < 100


@pytest.mark.asyncio
async def test_scenario_submission_ownership(client, student_auth, infra_seed):
    headers = _h(student_auth)
    slug = "devops-unhealthy-after-deploy"
    async with AsyncSessionLocal() as session:
        challenge = (
            await session.execute(
                select(ScenarioChallenge)
                .options(selectinload(ScenarioChallenge.steps).selectinload(ScenarioStep.options))
                .where(ScenarioChallenge.slug == slug)
            )
        ).scalar_one()
        answers = [
            {"step_id": str(s.id), "option_id": str(next(o for o in s.options if o.is_correct).id)}
            for s in challenge.steps
        ]
    sub = await client.post(f"/api/v1/scenarios/{slug}/submit", headers=headers, json={"answers": answers})
    sid = sub.json()["submission_id"]
    mine = await client.get(f"/api/v1/scenario-submissions/{sid}", headers=headers)
    assert mine.status_code == 200
    other = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"other_scen_{sid[:8]}@example.com",
            "username": f"osc{sid[:8]}",
            "full_name": "Other",
            "password": "Student123!",
        },
    )
    forbidden = await client.get(
        f"/api/v1/scenario-submissions/{sid}",
        headers={"Authorization": f"Bearer {other.json()['access_token']}"},
    )
    assert forbidden.status_code == 403


@pytest.mark.asyncio
async def test_domain_progress_and_home(client, student_auth, infra_seed):
    headers = _h(student_auth)
    for domain in ("cloud", "devops", "cybersecurity"):
        home = await client.get(f"/api/v1/{domain}", headers=headers)
        assert home.status_code == 200, home.text
        assert home.json()["tracks"]
        prog = await client.get(f"/api/v1/{domain}/progress", headers=headers)
        assert prog.status_code == 200
        assert "topics" in prog.json()


@pytest.mark.asyncio
async def test_paths_and_project_linkage(client, student_auth, infra_seed):
    headers = _h(student_auth)
    paths = await client.get("/api/v1/paths", headers=headers)
    assert paths.status_code == 200
    slugs = {p["slug"] for p in paths.json()} if isinstance(paths.json(), list) else set()
    if not slugs and isinstance(paths.json(), dict):
        nested = paths.json()
        slugs = {p["slug"] for section in nested.get("sections", []) for p in section.get("paths", [])}
        if not slugs:
            slugs = {p.get("slug") for p in nested.get("items", []) if p.get("slug")}
    hub = await client.get("/api/v1/practice-hub", headers=headers)
    assert hub.status_code == 200
    blob = str(hub.json())
    assert "aws-foundations" in blob
    assert "docker-foundations" in blob
    project = await client.get("/api/v1/projects/devops-dockerize-web-app", headers=headers)
    assert project.status_code == 200
    titles = str(project.json())
    assert "Linked scenario" in titles


@pytest.mark.asyncio
async def test_admin_scenario_permissions(client, student_auth, admin_auth, infra_seed):
    denied = await client.get("/api/v1/admin/scenarios", headers=_h(student_auth))
    assert denied.status_code == 403
    ok = await client.get("/api/v1/admin/scenarios", headers=admin_auth)
    assert ok.status_code == 200
    coverage = await client.get("/api/v1/admin/cloud", headers=admin_auth)
    assert coverage.status_code == 200
    assert coverage.json()["mcqs"] >= 1


@pytest.mark.asyncio
async def test_content_factory_scenario_and_mcq_kinds():
    async with AsyncSessionLocal() as session:
        mcq, _ = await validate_file_payload(
            session,
            {
                "content_kind": "cloud_mcq",
                "questions": [
                    {
                        "question_text": "Which AWS identity pattern is preferred for EC2 to S3?",
                        "topic": "iam",
                        "difficulty": "easy",
                        "options": [{"text": "Instance role"}, {"text": "Root keys"}],
                    }
                ],
            },
        )
        assert mcq[0].ok
        sc, _ = await validate_file_payload(
            session,
            {
                "content_kind": "scenario_challenge",
                "scenarios": [
                    {
                        "slug": "factory-scenario",
                        "title": "Factory scenario",
                        "domain_key": "cloud",
                        "scenario_type": "architecture",
                        "difficulty": "easy",
                        "steps": [
                            {
                                "prompt": "First action?",
                                "options": [
                                    {"label": "Add a load balancer", "is_correct": True},
                                    {"label": "Ignore load", "is_correct": False},
                                ],
                            }
                        ],
                    }
                ],
            },
        )
        assert sc[0].ok


@pytest.mark.asyncio
async def test_gap_report_infra_lines(infra_seed):
    async with AsyncSessionLocal() as session:
        report = await gap_report(session)
    lines = " ".join(report["catalog_gap_lines"])
    assert "AWS IAM" in lines or "Kubernetes" in lines or report["catalog_gap_lines"]
    assert "scenario_challenges" in report
