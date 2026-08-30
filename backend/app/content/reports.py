# ruff: noqa: E501
"""Coverage and daily summary reports for the Content Factory."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.interview import (
    ContentGenerationCandidate,
    InterviewQuestion,
    InterviewQuestionCompany,
    InterviewQuestionRole,
    InterviewQuestionSkill,
)
from app.models.interview_enums import ContentReviewStatus
from app.models.tagging import Company, JobRole, Skill

PRIORITY_SKILLS = [
    "SQL",
    "Python",
    "Spark",
    "Airflow",
    "AWS",
    "Snowflake",
    "Prompt Engineering",
    "RAG",
    "Agents",
    "MCP",
]


async def gap_report(session: AsyncSession) -> dict[str, Any]:
    roles = (await session.execute(select(JobRole).order_by(JobRole.name))).scalars().all()
    skills = (await session.execute(select(Skill).order_by(Skill.name))).scalars().all()

    live_filter = InterviewQuestion.review_status == ContentReviewStatus.APPROVED
    live_filter = live_filter & (InterviewQuestion.is_active.is_(True))

    by_role: list[dict[str, Any]] = []
    suggestions: list[str] = []
    for role in roles:
        skill_counts: dict[str, int] = {}
        for skill in skills:
            count = await session.scalar(
                select(func.count())
                .select_from(InterviewQuestion)
                .join(InterviewQuestionRole, InterviewQuestionRole.question_id == InterviewQuestion.id)
                .join(InterviewQuestionSkill, InterviewQuestionSkill.question_id == InterviewQuestion.id)
                .where(
                    live_filter,
                    InterviewQuestionRole.role_id == role.id,
                    InterviewQuestionSkill.skill_id == skill.id,
                )
            )
            n = int(count or 0)
            if n or skill.name in PRIORITY_SKILLS:
                skill_counts[skill.name] = n
        weak = [name for name, n in skill_counts.items() if n < 10 and name in PRIORITY_SKILLS]
        if weak:
            suggestions.append(f"{role.name}: generate more on {', '.join(weak)}")
        by_role.append(
            {
                "role": role.name,
                "skills": skill_counts,
                "total": sum(skill_counts.values()),
            }
        )

    pending = await session.scalar(
        select(func.count()).select_from(ContentGenerationCandidate).where(
            ContentGenerationCandidate.review_status == ContentReviewStatus.PENDING
        )
    )
    live = await session.scalar(
        select(func.count()).select_from(InterviewQuestion).where(live_filter)
    )

    from app.models.learn import CourseLesson, PracticePath, Project
    from app.models.question import Question
    from app.models.taxonomy import Domain

    project_rows = (
        await session.execute(
            select(Project.category_key, func.count(Project.id))
            .where(Project.is_published.is_(True))
            .group_by(Project.category_key)
        )
    ).all()
    projects_by_category = {key: int(n) for key, n in project_rows}

    path_rows = (
        await session.execute(
            select(PracticePath.path_type, func.count(PracticePath.id))
            .where(PracticePath.is_active.is_(True))
            .group_by(PracticePath.path_type)
        )
    ).all()
    paths_by_type = {str(getattr(k, "value", k)): int(n) for k, n in path_rows}

    lesson_count = int(await session.scalar(select(func.count()).select_from(CourseLesson)) or 0)
    mcq_count = int(await session.scalar(select(func.count()).select_from(Question)) or 0)
    domain_rows = (
        await session.execute(
            select(Domain.name, func.count(Question.id))
            .join(Question, Question.domain_id == Domain.id, isouter=True)
            .group_by(Domain.name)
        )
    ).all()

    catalog_gaps = []
    for label, key, target in [
        ("Python Projects", "python", 8),
        ("SQL Projects", "sql", 4),
        ("GenAI Projects", "generative-ai", 4),
        ("Java Projects", "java", 4),
        ("C++ Projects", "cpp", 4),
        ("JavaScript Projects", "javascript", 4),
    ]:
        n = projects_by_category.get(key, 0)
        if n < target:
            catalog_gaps.append(f"{label}: {n}")

    return {
        "live_questions": int(live or 0),
        "pending_candidates": int(pending or 0),
        "by_role": by_role,
        "suggested_priorities": suggestions or ["Add interview Q&A for high-demand skills (SQL, Python, RAG)."],
        "projects_by_category": projects_by_category,
        "paths_by_type": paths_by_type,
        "lessons": lesson_count,
        "mcq_questions": mcq_count,
        "mcq_by_domain": {name: int(n or 0) for name, n in domain_rows},
        "catalog_gap_lines": catalog_gaps or ["Catalog coverage looks healthy for current targets."],
    }


async def daily_report(session: AsyncSession) -> dict[str, Any]:
    now = datetime.now(UTC)
    start = datetime(now.year, now.month, now.day, tzinfo=UTC)
    live_filter = (InterviewQuestion.review_status == ContentReviewStatus.APPROVED) & (
        InterviewQuestion.is_active.is_(True)
    )
    live = await session.scalar(select(func.count()).select_from(InterviewQuestion).where(live_filter))
    pending = await session.scalar(
        select(func.count()).select_from(ContentGenerationCandidate).where(
            ContentGenerationCandidate.review_status == ContentReviewStatus.PENDING
        )
    )
    added_today = await session.scalar(
        select(func.count()).select_from(InterviewQuestion).where(
            live_filter, InterviewQuestion.reviewed_at >= start
        )
    )
    rejected_today = await session.scalar(
        select(func.count()).select_from(ContentGenerationCandidate).where(
            ContentGenerationCandidate.review_status == ContentReviewStatus.REJECTED,
            ContentGenerationCandidate.updated_at >= start,
        )
    )
    invalid_today = await session.scalar(
        select(func.count()).select_from(ContentGenerationCandidate).where(
            ContentGenerationCandidate.updated_at >= start,
            ContentGenerationCandidate.validation_errors.is_not(None),
        )
    )

    role_rows = (
        await session.execute(
            select(JobRole.name, func.count(InterviewQuestion.id))
            .join(InterviewQuestionRole, InterviewQuestionRole.role_id == JobRole.id)
            .join(InterviewQuestion, InterviewQuestion.id == InterviewQuestionRole.question_id)
            .where(live_filter)
            .group_by(JobRole.name)
            .order_by(func.count(InterviewQuestion.id).desc())
        )
    ).all()
    skill_rows = (
        await session.execute(
            select(Skill.name, func.count(InterviewQuestion.id))
            .join(InterviewQuestionSkill, InterviewQuestionSkill.skill_id == Skill.id)
            .join(InterviewQuestion, InterviewQuestion.id == InterviewQuestionSkill.question_id)
            .where(live_filter)
            .group_by(Skill.name)
            .order_by(func.count(InterviewQuestion.id).desc())
        )
    ).all()
    company_rows = (
        await session.execute(
            select(Company.name, func.count(InterviewQuestion.id))
            .join(InterviewQuestionCompany, InterviewQuestionCompany.company_id == Company.id)
            .join(InterviewQuestion, InterviewQuestion.id == InterviewQuestionCompany.question_id)
            .where(live_filter)
            .group_by(Company.name)
            .order_by(func.count(InterviewQuestion.id).desc())
        )
    ).all()

    gaps = await gap_report(session)
    return {
        "as_of": now.isoformat(),
        "live_interview_qa": int(live or 0),
        "pending_candidates": int(pending or 0),
        "questions_added_today": int(added_today or 0),
        "rejected_or_duplicate_flags_today": int(rejected_today or 0) + int(invalid_today or 0),
        "by_role": {name: int(c) for name, c in role_rows},
        "by_skill": {name: int(c) for name, c in skill_rows},
        "by_company": {name: int(c) for name, c in company_rows},
        "weak_coverage": gaps["suggested_priorities"],
    }
