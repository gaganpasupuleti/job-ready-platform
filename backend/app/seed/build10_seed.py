"""Build 10 role-skill requirements seed and E2E readiness fixtures."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.job import UserJobPreference
from app.models.readiness import RoleSkillRequirement
from app.models.readiness_enums import RoleSkillImportance, RoleSkillSource
from app.models.tagging import JobRole, Skill
from app.models.user import User
from app.seed.e2e import E2E_STUDENT_EMAIL

# role_slug -> [(skill_name, importance, weight)]
ROLE_SKILL_MAP: dict[str, list[tuple[str, RoleSkillImportance, float]]] = {
    "data-engineer": [
        ("SQL", RoleSkillImportance.CORE, 1.0),
        ("Python", RoleSkillImportance.CORE, 1.0),
        ("AWS", RoleSkillImportance.IMPORTANT, 0.9),
        ("Spark", RoleSkillImportance.IMPORTANT, 0.85),
        ("Snowflake", RoleSkillImportance.IMPORTANT, 0.8),
        ("Airflow", RoleSkillImportance.NICE_TO_HAVE, 0.5),
        ("Data Warehousing", RoleSkillImportance.NICE_TO_HAVE, 0.5),
    ],
    "data-analyst": [
        ("SQL", RoleSkillImportance.CORE, 1.0),
        ("Python", RoleSkillImportance.IMPORTANT, 0.8),
        ("Data Warehousing", RoleSkillImportance.IMPORTANT, 0.7),
    ],
    "genai-engineer": [
        ("RAG", RoleSkillImportance.CORE, 1.0),
        ("Prompt Engineering", RoleSkillImportance.CORE, 1.0),
        ("embeddings", RoleSkillImportance.IMPORTANT, 0.85),
        ("Agents", RoleSkillImportance.IMPORTANT, 0.8),
    ],
    "ai-agent-engineer": [
        ("Agents", RoleSkillImportance.CORE, 1.0),
        ("MCP", RoleSkillImportance.CORE, 0.95),
        ("Prompt Engineering", RoleSkillImportance.IMPORTANT, 0.9),
    ],
    "devops-engineer": [
        ("Linux", RoleSkillImportance.CORE, 1.0),
        ("Docker", RoleSkillImportance.CORE, 1.0),
        ("Kubernetes", RoleSkillImportance.IMPORTANT, 0.9),
        ("Terraform", RoleSkillImportance.IMPORTANT, 0.85),
        ("AWS", RoleSkillImportance.IMPORTANT, 0.8),
    ],
    "soc-analyst": [
        ("SOC", RoleSkillImportance.CORE, 1.0),
        ("IAM", RoleSkillImportance.IMPORTANT, 0.9),
        ("Incident Response", RoleSkillImportance.IMPORTANT, 0.85),
        ("Linux", RoleSkillImportance.IMPORTANT, 0.7),
    ],
    "cloud-engineer": [
        ("AWS", RoleSkillImportance.CORE, 1.0),
        ("Linux", RoleSkillImportance.CORE, 0.9),
        ("Docker", RoleSkillImportance.IMPORTANT, 0.8),
        ("Kubernetes", RoleSkillImportance.IMPORTANT, 0.8),
    ],
}


async def _skill_by_name(session, name: str) -> Skill | None:
    return (
        await session.execute(select(Skill).where(Skill.name.ilike(name)))
    ).scalar_one_or_none()


async def seed_build10_role_requirements() -> None:
    async with AsyncSessionLocal() as session:
        for role_slug, specs in ROLE_SKILL_MAP.items():
            role = (
                await session.execute(select(JobRole).where(JobRole.slug == role_slug))
            ).scalar_one_or_none()
            if role is None:
                continue
            for skill_name, importance, weight in specs:
                skill = await _skill_by_name(session, skill_name)
                if skill is None:
                    continue
                existing = (
                    await session.execute(
                        select(RoleSkillRequirement).where(
                            RoleSkillRequirement.role_id == role.id,
                            RoleSkillRequirement.skill_id == skill.id,
                        )
                    )
                ).scalar_one_or_none()
                if existing:
                    existing.importance = importance
                    existing.weight = weight
                else:
                    session.add(
                        RoleSkillRequirement(
                            role_id=role.id,
                            skill_id=skill.id,
                            importance=importance,
                            weight=weight,
                            source=RoleSkillSource.SEED,
                        )
                    )
        await session.commit()


async def seed_build10_e2e_preferences() -> None:
    """Set E2E student target role to Data Engineer."""
    async with AsyncSessionLocal() as session:
        user = (
            await session.execute(select(User).where(User.email == E2E_STUDENT_EMAIL))
        ).scalar_one_or_none()
        if user is None:
            return
        role = (
            await session.execute(select(JobRole).where(JobRole.slug == "data-engineer"))
        ).scalar_one_or_none()
        if role is None:
            return
        pref = (
            await session.execute(select(UserJobPreference).where(UserJobPreference.user_id == user.id))
        ).scalar_one_or_none()
        if pref is None:
            session.add(UserJobPreference(user_id=user.id, target_role_id=role.id, updated_at=datetime.now(UTC)))
        else:
            pref.target_role_id = role.id
            pref.updated_at = datetime.now(UTC)
        await session.commit()


async def seed_build10() -> None:
    await seed_build10_role_requirements()
    await seed_build10_e2e_preferences()
