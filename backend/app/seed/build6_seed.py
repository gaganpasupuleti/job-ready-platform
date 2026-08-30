"""Idempotent Build 6 seed: taxonomy, AI MCQs, prompt challenges, paths, project links."""

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
from app.models.prompt import PromptChallenge, PromptChallengeCase, PromptEvaluationRubric
from app.models.prompt_enums import PromptTaskType
from app.models.question import Question, QuestionOption
from app.models.tagging import JobRole, QuestionRole
from app.models.taxonomy import Category, Domain, Topic
from app.seed.build6_challenges import PROMPT_CHALLENGES
from app.seed.build6_mcq import AI_MCQS
from app.seed.taxonomy_data import JOB_ROLES, TAXONOMY


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


TOPIC_ROLES = {
    "llm-fundamentals": ["GenAI Engineer", "AI Engineer"],
    "transformers": ["ML Engineer", "GenAI Engineer"],
    "embeddings": ["RAG Engineer", "ML Engineer"],
    "vector-databases": ["RAG Engineer", "AI Engineer"],
    "rag": ["RAG Engineer", "GenAI Engineer"],
    "retrieval": ["RAG Engineer"],
    "tool-calling": ["AI Agent Engineer", "AI Application Developer"],
    "llm-evaluation": ["GenAI Engineer", "ML Engineer"],
    "ai-security": ["AI Engineer", "Cloud AI Engineer"],
    "ai-system-design": ["AI Engineer", "Cloud AI Engineer"],
    "instruction-design": ["Prompt Engineer"],
    "zero-shot": ["Prompt Engineer"],
    "few-shot": ["Prompt Engineer"],
    "structured-outputs": ["Prompt Engineer", "AI Application Developer"],
    "context-engineering": ["Prompt Engineer", "RAG Engineer"],
    "prompt-injection": ["Prompt Engineer", "AI Engineer"],
    "prompt-evaluation": ["Prompt Engineer"],
    "agent-fundamentals": ["AI Agent Engineer"],
    "agent-loops": ["AI Agent Engineer"],
    "multi-agent-systems": ["AI Agent Engineer"],
    "mcp-fundamentals": ["AI Agent Engineer", "AI Application Developer"],
}

PATH_SPECS = [
    ("ai-generative-ai", "Generative AI", "LLM fundamentals, transformers, and embeddings MCQs.", "/ai/genai", ["llm-fundamentals", "transformers", "embeddings"]),
    ("ai-rag", "RAG", "Ingestion, retrieval, grounding, and production RAG scenarios.", "/ai/rag", ["rag", "retrieval", "vector-databases"]),
    ("ai-prompt-engineering", "Prompt Engineering", "Theory MCQs plus interactive prompt challenges.", "/ai/prompt-engineering", ["instruction-design", "few-shot", "structured-outputs"]),
    ("ai-agents", "AI Agents", "Agent loops, tools, and orchestration scenarios.", "/ai/agents", ["agent-fundamentals", "agent-loops"]),
    ("ai-mcp", "MCP", "Host, client, server, tools, and security concepts.", "/ai/mcp", ["mcp-fundamentals"]),
    ("ai-security", "AI Security", "Prompt injection, tool risk, and RAG trust boundaries.", "/ai/security", ["ai-security", "prompt-injection"]),
]

PROJECT_LINKS = {
    "genai-faq-rag-assistant": ("rag-citation-instruction", "rag"),
    "genai-resume-skill-extractor": ("resume-skill-extractor", "structured-outputs"),
    "genai-document-qa": ("rag-citation-instruction", "rag"),
    "genai-prompt-classifier": ("support-ticket-classifier", "instruction-design"),
    "genai-support-ticket-router": ("routing-prompt", "tool-calling"),
    "genai-ai-agent-workflow": ("agent-instruction-prompt", "agent-fundamentals"),
}


async def seed_build6_content() -> None:
    async with AsyncSessionLocal() as session:
        await _ensure_taxonomy(session)
        await _ensure_roles(session)
        await _seed_mcqs(session)
        await _seed_challenges(session)
        await _seed_paths(session)
        await _wire_projects(session)
        await session.commit()
        print("Build 6 AI practice content seeded.")


async def _ensure_taxonomy(session) -> None:
    for domain_data in TAXONOMY:
        if domain_data["slug"] != "ai":
            continue
        domain = (await session.execute(select(Domain).where(Domain.slug == "ai"))).scalar_one_or_none()
        if domain is None:
            domain = Domain(name="AI", slug="ai", description="AI domain", is_active=True)
            session.add(domain)
            await session.flush()
        for cat in domain_data["categories"]:
            category = (
                await session.execute(
                    select(Category).where(Category.slug == cat["slug"], Category.domain_id == domain.id)
                )
            ).scalar_one_or_none()
            if category is None:
                category = Category(
                    name=cat["name"], slug=cat["slug"], domain_id=domain.id, is_active=True
                )
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


async def _seed_mcqs(session) -> None:
    domain = (await session.execute(select(Domain).where(Domain.slug == "ai"))).scalar_one()
    cats = {
        c.slug: c
        for c in (await session.execute(select(Category).where(Category.domain_id == domain.id))).scalars().all()
    }
    topics = (await session.execute(select(Topic))).scalars().all()
    topic_map = {(t.category_id, t.slug): t for t in topics}
    roles = {r.name: r for r in (await session.execute(select(JobRole))).scalars().all()}
    existing_texts = set((await session.execute(select(Question.question_text))).scalars().all())

    for cat_slug, topic_slug, difficulty, text, expl, correct, w1, w2, w3 in AI_MCQS:
        if text in existing_texts:
            continue
        category = cats[cat_slug]
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
            session.add(QuestionOption(id=uuid4(), question_id=question.id, option_text=opt, is_correct=ok, sort_order=idx))
        for role_name in TOPIC_ROLES.get(topic_slug, ["AI Engineer"]):
            role = roles.get(role_name)
            if role:
                session.add(QuestionRole(question_id=question.id, role_id=role.id))
        existing_texts.add(text)


async def _seed_challenges(session) -> None:
    for spec in PROMPT_CHALLENGES:
        existing = (
            await session.execute(select(PromptChallenge).where(PromptChallenge.slug == spec["slug"]))
        ).scalar_one_or_none()
        if existing is not None:
            existing.is_active = True
            continue
        challenge = PromptChallenge(
            slug=spec["slug"],
            title=spec["title"],
            description=spec["description"],
            difficulty=Difficulty(spec["difficulty"]),
            task_type=PromptTaskType(spec["task_type"]),
            scenario=spec["scenario"],
            instructions=spec["instructions"],
            input_description=spec["input_description"],
            expected_behavior=spec["expected_behavior"],
            starter_prompt=spec["starter_prompt"],
            max_prompt_length=spec["max_prompt_length"],
            mastery_threshold=spec["mastery_threshold"],
            rubric_weights=spec["rubric_weights"],
            hints=spec["hints"],
            common_mistakes=spec["common_mistakes"],
            evaluation_criteria_summary=spec["evaluation_criteria_summary"],
            is_active=True,
        )
        session.add(challenge)
        await session.flush()
        for dim, weight in spec["rubric_weights"].items():
            session.add(PromptEvaluationRubric(challenge_id=challenge.id, dimension=dim, weight=weight))
        for idx, case in enumerate(spec["cases"]):
            session.add(
                PromptChallengeCase(
                    challenge_id=challenge.id,
                    input_text=case.get("input_text") or "",
                    variables=case.get("variables") or {},
                    evaluation_config=case.get("evaluation_config") or {},
                    is_hidden=bool(case.get("is_hidden")),
                    hide_input=bool(case.get("hide_input")),
                    weight=float(case.get("weight") or 1),
                    sort_order=idx,
                )
            )


async def _seed_paths(session) -> None:
    topics = {t.slug: t for t in (await session.execute(select(Topic))).scalars().all()}
    for slug, title, short, href, topic_slugs in PATH_SPECS:
        path = (await session.execute(select(PracticePath).where(PracticePath.slug == slug))).scalar_one_or_none()
        if path is None:
            path = PracticePath(
                slug=slug,
                title=title,
                short_description=short,
                description=short,
                path_type=PracticePathType.AI,
                difficulty=PracticePathDifficulty.BEGINNER,
                availability=PathAvailability.AVAILABLE,
                is_active=True,
                sort_order=80,
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
        if slug == "ai-prompt-engineering":
            session.add(
                PracticePathItem(
                    section_id=section.id,
                    item_type=PracticePathItemType.EXTERNAL_ROUTE,
                    title="Prompt challenges",
                    sort_order=50,
                    external_route="/ai/prompt-engineering/challenges",
                )
            )


async def _wire_projects(session) -> None:
    topics = {t.slug: t for t in (await session.execute(select(Topic))).scalars().all()}
    for project_slug, (challenge_slug, topic_slug) in PROJECT_LINKS.items():
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
        marker = f"prompt:{challenge_slug}"
        already = await session.scalar(
            select(ProjectTask.id).where(
                ProjectTask.module_id == module.id,
                ProjectTask.title == f"Linked prompt challenge: {challenge_slug}",
            )
        )
        if already:
            continue
        topic = topics.get(topic_slug)
        session.add(
            ProjectTask(
                module_id=module.id,
                title=f"Linked prompt challenge: {challenge_slug}",
                sort_order=40,
                task_type=ProjectTaskType.MCQ,
                topic_id=topic.id if topic else None,
                summary=f"Practice without a live LLM. {marker}",
                body_json={
                    "blocks": [
                        {
                            "type": "text",
                            "value": f"Open /ai/prompt-engineering/challenges/{challenge_slug} and related MCQs. No external model required.",
                        }
                    ]
                },
                estimated_minutes=20,
            )
        )


if __name__ == "__main__":
    import asyncio

    asyncio.run(seed_build6_content())
