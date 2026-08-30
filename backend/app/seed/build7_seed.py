"""Idempotent Build 7 seed: taxonomy, MCQs, scenarios, paths, project links."""

from __future__ import annotations

from uuid import uuid4

import re

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.enums import Difficulty, QuestionType
from app.models.learn import PracticePath, PracticePathItem, PracticePathSection, Project, ProjectModule, ProjectTask
from app.models.learn_enums import (
    PathAvailability,
    PracticePathDifficulty,
    PracticePathItemType,
    PracticePathType,
    ProjectTaskType,
)
from app.models.question import Question, QuestionOption
from app.models.scenario import ScenarioChallenge, ScenarioOption, ScenarioStep
from app.models.scenario_enums import ScenarioDomain, ScenarioType
from app.models.tagging import JobRole, QuestionRole
from app.models.taxonomy import Category, Domain, Topic
from app.seed.build7_mcq import CLOUD_MCQS, CYBER_MCQS, DEVOPS_MCQS
from app.seed.build7_scenarios import SCENARIOS
from app.seed.taxonomy_data import JOB_ROLES, TAXONOMY
from app.services.catalog_cache_service import CatalogCacheService


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


DOMAIN_SLUGS = ("cloud", "devops", "cybersecurity")

TOPIC_ROLES = {
    "iam": ["AWS Engineer", "Cloud Engineer"],
    "ec2": ["AWS Engineer", "Cloud Engineer"],
    "s3": ["AWS Engineer"],
    "vpc": ["AWS Engineer", "Cloud Engineer"],
    "lambda": ["AWS Engineer"],
    "entra-id": ["Azure Engineer"],
    "rbac": ["Azure Engineer", "Cloud Security Engineer"],
    "gcp-iam": ["Cloud Engineer"],
    "compute-engine": ["Cloud Engineer"],
    "dockerfile": ["DevOps Engineer", "Platform Engineer"],
    "compose": ["DevOps Engineer"],
    "pod": ["DevOps Engineer", "Platform Engineer"],
    "deployment": ["DevOps Engineer"],
    "pipeline-stages": ["DevOps Engineer"],
    "state": ["DevOps Engineer", "Platform Engineer"],
    "cia-triad": ["Cybersecurity Analyst", "Security Engineer"],
    "owasp": ["Security Engineer", "DevSecOps Engineer"],
    "siem": ["SOC Analyst"],
    "containment": ["SOC Analyst", "Cybersecurity Analyst"],
    "object-level-authorization": ["Security Engineer", "DevSecOps Engineer"],
}

PATH_SPECS: list[tuple] = [
    ("aws-foundations", "AWS Foundations", "Unofficial preparation for AWS foundational knowledge.", "/cloud/aws", PracticePathType.CLOUD, ["iam", "ec2", "s3", "vpc"], "cloud-traffic-surge-single-server"),
    ("aws-engineer", "AWS Engineer", "Job-oriented AWS networking, compute, and security MCQs plus scenarios.", "/cloud/aws", PracticePathType.CLOUD, ["iam", "vpc", "lambda", "cloudwatch"], "cloud-private-db-exposure"),
    ("azure-foundations", "Azure Foundations", "Unofficial Azure foundational practice.", "/cloud/azure", PracticePathType.CLOUD, ["entra-id", "virtual-machines", "blob-storage", "rbac"], None),
    ("gcp-foundations", "GCP Foundations", "Unofficial GCP foundational practice.", "/cloud/gcp", PracticePathType.CLOUD, ["gcp-iam", "compute-engine", "cloud-storage", "gke"], None),
    ("linux-foundations", "Linux", "Filesystem, permissions, processes, and logs.", "/devops/linux", PracticePathType.DEVOPS, ["permissions", "processes", "logs"], "devops-linux-disk-full"),
    ("docker-foundations", "Docker", "Images, Dockerfile, Compose, and container security.", "/devops/docker", PracticePathType.DEVOPS, ["dockerfile", "compose", "images"], "devops-unhealthy-after-deploy"),
    ("kubernetes-foundations", "Kubernetes", "Pods, Deployments, Services — no live cluster.", "/devops/kubernetes", PracticePathType.DEVOPS, ["pod", "deployment", "service"], "devops-k8s-crashloop"),
    ("cicd-foundations", "CI/CD", "Pipelines, artifacts, secrets, and rollback.", "/devops/cicd", PracticePathType.DEVOPS, ["pipeline-stages", "rollback", "cicd-secrets"], "devops-pipeline-secret-in-logs"),
    ("terraform-foundations", "Terraform", "IaC, state, and plan/apply — no live providers.", "/devops/terraform", PracticePathType.DEVOPS, ["state", "plan-apply", "modules"], "devops-terraform-state-in-git"),
    ("devops-engineer", "DevOps Engineer", "Linux through observability for platform roles.", "/devops", PracticePathType.DEVOPS, ["dockerfile", "pod", "pipeline-stages"], "devops-unhealthy-after-deploy"),
    ("cyber-foundations", "Cybersecurity Foundations", "CIA, IAM, and defensive fundamentals.", "/cybersecurity/fundamentals", PracticePathType.CYBERSECURITY, ["cia-triad", "least-privilege", "zero-trust"], None),
    ("soc-analyst", "SOC Analyst", "Alerts, SIEM concepts, and triage.", "/cybersecurity/soc", PracticePathType.CYBERSECURITY, ["soc-roles", "siem", "triage"], "cyber-failed-then-success-login"),
    ("cloud-security-path", "Cloud Security", "Identity, storage exposure, and logging.", "/cloud/security", PracticePathType.CYBERSECURITY, ["cloud-identity", "data-protection"], "cyber-public-bucket-findings"),
    ("web-api-security", "Web/API Security", "OWASP concepts and API authorization — defensive only.", "/cybersecurity/web-security", PracticePathType.CYBERSECURITY, ["owasp", "object-level-authorization"], "cyber-api-idor-review"),
    ("devsecops-path", "DevSecOps", "Secure pipelines, secrets, and image provenance.", "/devops/cicd", PracticePathType.CYBERSECURITY, ["cicd-secrets", "container-security"], "cyber-devsecops-pipeline-unsigned"),
]

PROJECT_LINKS = [
    ("devops-dockerize-web-app", "dockerfile", "devops-unhealthy-after-deploy", "/devops/docker"),
    ("devops-cicd-pipeline-design", "pipeline-stages", "devops-blue-green-failed-health", "/devops/cicd"),
    ("devops-compose-multi-service", "compose", "devops-unhealthy-after-deploy", "/devops/docker"),
    ("devops-monitoring-basics", "metrics", "devops-missing-metrics", "/devops/observability"),
    ("cloud-aws-web-app", "ha-web-app", "cloud-traffic-surge-single-server", "/cloud/architecture"),
    ("cloud-aws-iam-access", "iam", "cloud-private-db-exposure", "/cloud/aws"),
    ("cloud-aws-serverless-api", "lambda", "cloud-serverless-timeouts", "/cloud/aws"),
    ("cyber-incident-response-scenario", "containment", "cyber-failed-then-success-login", "/cybersecurity/incident-response"),
    ("cyber-owasp-risk-identification", "owasp", "cyber-xss-report", "/cybersecurity/owasp"),
    ("cyber-api-security-review", "object-level-authorization", "cyber-api-idor-review", "/cybersecurity/api-security"),
]


async def seed_build7_content() -> None:
    async with AsyncSessionLocal() as session:
        await _ensure_taxonomy(session)
        await _ensure_roles(session)
        await _seed_mcqs(session, "cloud", CLOUD_MCQS)
        await _seed_mcqs(session, "devops", DEVOPS_MCQS)
        await _seed_mcqs(session, "cybersecurity", CYBER_MCQS)
        await _seed_scenarios(session)
        await _seed_paths(session)
        await _wire_projects(session)
        await session.commit()
    await CatalogCacheService().invalidate()
    print("Build 7 cloud/devops/cyber practice content seeded.")


async def _ensure_taxonomy(session) -> None:
    for domain_data in TAXONOMY:
        if domain_data["slug"] not in DOMAIN_SLUGS:
            continue
        domain = (
            await session.execute(select(Domain).where(Domain.slug == domain_data["slug"]))
        ).scalar_one_or_none()
        if domain is None:
            domain = Domain(
                name=domain_data["name"],
                slug=domain_data["slug"],
                description=f"{domain_data['name']} practice domain",
                is_active=True,
            )
            session.add(domain)
            await session.flush()
        for cat in domain_data["categories"]:
            category = (
                await session.execute(
                    select(Category).where(Category.slug == cat["slug"], Category.domain_id == domain.id)
                )
            ).scalar_one_or_none()
            if category is None:
                category = Category(name=cat["name"], slug=cat["slug"], domain_id=domain.id, is_active=True)
                session.add(category)
                await session.flush()
            for topic in cat["topics"]:
                existing = (
                    await session.execute(
                        select(Topic).where(Topic.slug == topic["slug"], Topic.category_id == category.id)
                    )
                ).scalar_one_or_none()
                if existing is None:
                    session.add(
                        Topic(name=topic["name"], slug=topic["slug"], category_id=category.id, is_active=True)
                    )
        await session.flush()


async def _ensure_roles(session) -> None:
    for name in JOB_ROLES:
        row = (await session.execute(select(JobRole).where(JobRole.slug == slugify(name)))).scalar_one_or_none()
        if row is None:
            session.add(JobRole(name=name, slug=slugify(name)))
    await session.flush()


async def _seed_mcqs(session, domain_slug: str, rows: list) -> None:
    domain = (await session.execute(select(Domain).where(Domain.slug == domain_slug))).scalar_one()
    cats = {
        c.slug: c
        for c in (await session.execute(select(Category).where(Category.domain_id == domain.id))).scalars().all()
    }
    topics = (await session.execute(select(Topic))).scalars().all()
    topic_map = {(t.category_id, t.slug): t for t in topics}
    roles = {r.name: r for r in (await session.execute(select(JobRole))).scalars().all()}
    existing_texts = set((await session.execute(select(Question.question_text))).scalars().all())
    defaults = {
        "cloud": ["Cloud Engineer"],
        "devops": ["DevOps Engineer"],
        "cybersecurity": ["Cybersecurity Analyst"],
    }

    for cat_slug, topic_slug, difficulty, text, expl, correct, w1, w2, w3 in rows:
        if text in existing_texts:
            continue
        category = cats.get(cat_slug)
        if category is None:
            continue
        topic = topic_map.get((category.id, topic_slug))
        if topic is None:
            continue
        question = Question(
            question_type=QuestionType.SINGLE_CHOICE,
            question_text=text,
            explanation=expl,
            difficulty=Difficulty(difficulty),
            domain_id=domain.id,
            category_id=category.id,
            topic_id=topic.id,
            marks=1.0,
            negative_marks=0.25,
            estimated_time_seconds=90,
            is_active=True,
            is_premium=False,
            is_sample=True,
        )
        session.add(question)
        await session.flush()
        for idx, (opt, ok) in enumerate([(correct, True), (w1, False), (w2, False), (w3, False)]):
            session.add(
                QuestionOption(id=uuid4(), question_id=question.id, option_text=opt, is_correct=ok, sort_order=idx)
            )
        for role_name in TOPIC_ROLES.get(topic_slug, defaults[domain_slug]):
            role = roles.get(role_name)
            if role:
                session.add(QuestionRole(question_id=question.id, role_id=role.id))
        existing_texts.add(text)


async def _seed_scenarios(session) -> None:
    for spec in SCENARIOS:
        existing = (
            await session.execute(select(ScenarioChallenge).where(ScenarioChallenge.slug == spec["slug"]))
        ).scalar_one_or_none()
        if existing is not None:
            existing.is_active = True
            continue
        challenge = ScenarioChallenge(
            slug=spec["slug"],
            title=spec["title"],
            description=spec["description"],
            domain_key=ScenarioDomain(spec["domain_key"]),
            scenario_type=ScenarioType(spec["scenario_type"]),
            difficulty=Difficulty(spec["difficulty"]),
            context_text=spec["context_text"],
            evidence_json=spec["evidence_json"],
            unofficial_cert_tag=spec["unofficial_cert_tag"],
            mastery_threshold=spec["mastery_threshold"],
            is_active=True,
        )
        session.add(challenge)
        await session.flush()
        for idx, step in enumerate(spec["steps"]):
            row = ScenarioStep(
                challenge_id=challenge.id,
                sort_order=idx,
                prompt=step["prompt"],
                context_snippet=step.get("context_snippet") or "",
                is_critical=bool(step.get("is_critical")),
                explanation=step.get("explanation") or "",
                scoring_weight=float(step.get("scoring_weight") or 1),
            )
            session.add(row)
            await session.flush()
            for j, opt in enumerate(step.get("options") or []):
                session.add(
                    ScenarioOption(
                        step_id=row.id,
                        label=opt["label"],
                        is_correct=bool(opt.get("is_correct")),
                        explanation=opt.get("explanation") or "",
                        sort_order=j,
                    )
                )


async def _seed_paths(session) -> None:
    topics = {t.slug: t for t in (await session.execute(select(Topic))).scalars().all()}
    for slug, title, short, href, path_type, topic_slugs, scenario_slug in PATH_SPECS:
        path = (await session.execute(select(PracticePath).where(PracticePath.slug == slug))).scalar_one_or_none()
        if path is None:
            path = PracticePath(
                slug=slug,
                title=title,
                short_description=short,
                description=short + " Unofficial preparation. Not affiliated with any certification vendor.",
                path_type=path_type,
                difficulty=PracticePathDifficulty.BEGINNER,
                availability=PathAvailability.AVAILABLE,
                is_active=True,
                sort_order=90,
                external_route=href,
            )
            session.add(path)
            await session.flush()
        section = (
            await session.execute(
                select(PracticePathSection).where(
                    PracticePathSection.path_id == path.id, PracticePathSection.section_key == "practice"
                )
            )
        ).scalar_one_or_none()
        if section is None:
            section = PracticePathSection(path_id=path.id, title="Practice", section_key="practice", sort_order=0)
            session.add(section)
            await session.flush()
        has_item = await session.scalar(select(PracticePathItem.id).where(PracticePathItem.section_id == section.id).limit(1))
        if has_item:
            continue
        session.add(
            PracticePathItem(
                section_id=section.id,
                item_type=PracticePathItemType.EXTERNAL_ROUTE,
                title=f"Open {title}",
                sort_order=0,
                external_route=href,
            )
        )
        for idx, tslug in enumerate(topic_slugs, start=1):
            topic = topics.get(tslug)
            if topic is None:
                continue
            session.add(
                PracticePathItem(
                    section_id=section.id,
                    item_type=PracticePathItemType.MCQ_TOPIC,
                    title=f"MCQ: {topic.name}",
                    sort_order=idx,
                    topic_id=topic.id,
                )
            )
        if scenario_slug:
            session.add(
                PracticePathItem(
                    section_id=section.id,
                    item_type=PracticePathItemType.SCENARIO,
                    title=f"Scenario: {scenario_slug}",
                    sort_order=40,
                    external_route=f"/scenarios/{scenario_slug}",
                )
            )


async def _wire_projects(session) -> None:
    topics = {t.slug: t for t in (await session.execute(select(Topic))).scalars().all()}
    for project_slug, topic_slug, scenario_slug, lesson_href in PROJECT_LINKS:
        project = (await session.execute(select(Project).where(Project.slug == project_slug))).scalar_one_or_none()
        if project is None:
            continue
        module = (
            await session.execute(
                select(ProjectModule).where(ProjectModule.project_id == project.id).order_by(ProjectModule.sort_order)
            )
        ).scalars().first()
        if module is None:
            continue
        already = await session.scalar(
            select(ProjectTask.id).where(
                ProjectTask.module_id == module.id,
                ProjectTask.title == f"Linked scenario: {scenario_slug}",
            )
        )
        if already:
            continue
        topic = topics.get(topic_slug)
        session.add(
            ProjectTask(
                module_id=module.id,
                title=f"Related lessons / MCQ: {topic_slug}",
                sort_order=41,
                task_type=ProjectTaskType.MCQ,
                topic_id=topic.id if topic else None,
                summary=f"Practice the {topic_slug} MCQ topic. Track page: {lesson_href}",
            )
        )
        session.add(
            ProjectTask(
                module_id=module.id,
                title=f"Linked scenario: {scenario_slug}",
                sort_order=42,
                task_type=ProjectTaskType.CHECKLIST,
                summary=f"Complete deterministic scenario /scenarios/{scenario_slug}. No live cloud or cluster.",
            )
        )
