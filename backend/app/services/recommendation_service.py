"""Deterministic next-best-action recommendations."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.learn import PracticePath, UserProjectProgress
from app.models.readiness import MistakeItem
from app.models.readiness_enums import MistakeStatus, RoleSkillImportance
from app.models.tagging import Skill
from app.models.user import User
from app.services.readiness_service import ReadinessService
from app.services.skill_evidence_service import SkillEvidenceService


class RecommendationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.readiness = ReadinessService(db)
        self.evidence = SkillEvidenceService(db)

    async def get_recommendations(self, user: User, limit: int = 8) -> list[dict]:
        overview = await self.readiness.get_overview(user)
        actions: list[dict] = []
        seen_skills: set[str] = set()

        for skill_row in overview.get("skills", []):
            if skill_row["importance"] != RoleSkillImportance.CORE.value:
                continue
            if skill_row["status"] in ("strong",):
                continue
            slug = skill_row["skill_slug"].lower()
            if slug in seen_skills:
                continue
            seen_skills.add(slug)
            href, action_type = self._practice_route(slug)
            actions.append(
                {
                    "title": f"Practice {skill_row['skill_name']}",
                    "description": f"Build hands-on evidence for {skill_row['skill_name']}.",
                    "reason": (
                        f"{skill_row['skill_name']} is a core "
                        f"{overview.get('target_role', {}).get('name', 'target role')} skill and your current "
                        f"evidence is {skill_row['evidence_strength']} "
                        f"({skill_row['readiness']}% readiness)."
                    ),
                    "skill": skill_row["skill_name"],
                    "priority": "high" if skill_row["status"] == "missing" else "medium",
                    "href": href,
                    "action_type": action_type,
                    "score": 100 - float(skill_row.get("readiness") or 0),
                }
            )

        mistakes = (
            await self.db.execute(
                select(MistakeItem)
                .where(
                    MistakeItem.user_id == user.id,
                    MistakeItem.status != MistakeStatus.RESOLVED,
                    MistakeItem.occurrence_count >= 2,
                )
                .order_by(MistakeItem.occurrence_count.desc())
                .limit(3)
            )
        ).scalars().all()
        for m in mistakes:
            actions.append(
                {
                    "title": f"Review: {m.title}",
                    "description": "Repeated weak area from your mistake book.",
                    "reason": f"You missed this {m.occurrence_count} times recently.",
                    "skill": None,
                    "priority": "high",
                    "href": m.retry_href or "/mistakes",
                    "action_type": "review_mistakes",
                    "score": 50 + m.occurrence_count * 5,
                }
            )

        unfinished = (
            await self.db.execute(
                select(UserProjectProgress)
                .where(UserProjectProgress.user_id == user.id, UserProjectProgress.percent.between(40, 90))
                .order_by(UserProjectProgress.percent.desc())
                .limit(2)
            )
        ).scalars().all()
        for prog in unfinished:
            actions.append(
                {
                    "title": "Continue project",
                    "description": "Nearly complete — finish for stronger project evidence.",
                    "reason": f"Project is {prog.percent}% complete.",
                    "skill": None,
                    "priority": "medium",
                    "href": f"/projects/{prog.project_id}",
                    "action_type": "continue_project",
                    "score": prog.percent,
                }
            )

        actions.sort(key=lambda x: x.get("score", 0), reverse=True)
        deduped: list[dict] = []
        seen_hrefs: set[str] = set()
        for a in actions:
            if a["href"] in seen_hrefs:
                continue
            seen_hrefs.add(a["href"])
            deduped.append({k: v for k, v in a.items() if k != "score"})
            if len(deduped) >= limit:
                break
        return deduped

    def _practice_route(self, skill_slug: str) -> tuple[str, str]:
        routes = {
            "sql": ("/practice/sql", "practice_sql"),
            "python": ("/practice/coding", "practice_coding"),
            "aws": ("/cloud", "practice_scenario"),
            "azure": ("/cloud", "practice_scenario"),
            "docker": ("/devops", "practice_scenario"),
            "kubernetes": ("/devops", "practice_scenario"),
            "rag": ("/ai", "practice_prompt"),
            "prompt-engineering": ("/ai", "practice_prompt"),
            "agents": ("/ai", "practice_prompt"),
            "mcp": ("/ai", "practice_prompt"),
            "soc": ("/cybersecurity", "practice_scenario"),
            "snowflake": ("/practice/sql", "practice_sql"),
            "spark": ("/interviews/packs/data-engineer-intermediate", "interview_pack"),
        }
        return routes.get(skill_slug, ("/practice", "practice_mcq"))
