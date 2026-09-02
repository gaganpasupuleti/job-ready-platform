"""Deterministic job requirement coverage — not hiring probability."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job, JobRoleMap, JobSkill, UserJobPreference
from app.models.job_enums import JobSkillImportance
from app.models.tagging import JobRole, Skill
from app.models.user import User
from app.readiness.formulas import (
    JOB_MATCH_WEIGHTS,
    MIN_JOB_MAPPED_SKILLS,
    coverage_status,
    weighted_average,
)
from app.services.skill_evidence_service import SkillEvidenceService


class JobMatchService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.evidence = SkillEvidenceService(db)

    async def _skill_readiness(self, user_id: UUID, skill_id: UUID, evidence_map) -> float:
        for ev in evidence_map.values():
            if ev.skill_id == skill_id:
                return ev.effective_score
        return 0.0

    async def match_job(self, user: User, job_id: UUID) -> dict:
        job = await self.db.get(Job, job_id)
        if job is None:
            return {"error": "Job not found"}

        job_skills = (
            await self.db.execute(
                select(JobSkill, Skill)
                .join(Skill, Skill.id == JobSkill.skill_id)
                .where(JobSkill.job_id == job_id)
            )
        ).all()

        if len(job_skills) < MIN_JOB_MAPPED_SKILLS:
            return {
                "coverage": None,
                "has_sufficient_mapping": False,
                "has_user_evidence": False,
                "message": "Not enough mapped requirements for this job.",
                "required": [],
                "preferred": [],
                "why": [],
            }

        evidence_map = await self.evidence.collect_all(user.id)
        total_activity = sum(e.activity_count for e in evidence_map.values())
        has_evidence = total_activity > 0

        required_rows: list[dict] = []
        preferred_rows: list[dict] = []
        req_weighted: list[tuple[float, float]] = []
        pref_weighted: list[tuple[float, float]] = []

        for js, skill in job_skills:
            imp = js.importance.value if hasattr(js.importance, "value") else str(js.importance)
            readiness = await self._skill_readiness(user.id, skill.id, evidence_map)
            row = {
                "skill_id": str(skill.id),
                "skill": skill.name,
                "readiness": readiness,
                "status": coverage_status(readiness),
            }
            if imp in (JobSkillImportance.REQUIRED.value, "required"):
                required_rows.append(row)
                req_weighted.append((readiness, 1.0))
            else:
                preferred_rows.append(row)
                pref_weighted.append((readiness, 1.0))

        required_score = weighted_average(req_weighted) if req_weighted else 0.0
        preferred_score = weighted_average(pref_weighted) if pref_weighted else 0.0

        role_score = 0.0
        pref = (
            await self.db.execute(select(UserJobPreference).where(UserJobPreference.user_id == user.id))
        ).scalar_one_or_none()
        if pref and pref.target_role_id:
            role_maps = (
                await self.db.execute(select(JobRoleMap).where(JobRoleMap.job_id == job_id))
            ).scalars().all()
            if any(m.role_id == pref.target_role_id for m in role_maps):
                role_score = 100.0

        preference_score = 0.0
        if pref:
            if pref.remote_preference and job.is_remote:
                preference_score = 100.0
            elif pref.preferred_locations_json and job.city:
                locs = pref.preferred_locations_json or []
                if any(job.city.lower() in str(loc).lower() for loc in locs):
                    preference_score = 100.0

        if not has_evidence:
            return {
                "coverage": None,
                "has_sufficient_mapping": True,
                "has_user_evidence": False,
                "message": "Requirements available — complete practice to compare your current evidence.",
                "required": required_rows,
                "preferred": preferred_rows,
                "why": [],
            }

        coverage = round(
            required_score * JOB_MATCH_WEIGHTS["required"]
            + preferred_score * JOB_MATCH_WEIGHTS["preferred"]
            + role_score * JOB_MATCH_WEIGHTS["role"]
            + preference_score * JOB_MATCH_WEIGHTS["preference"],
            1,
        )

        why = [
            {
                "factor": "required_skills",
                "weight_percent": JOB_MATCH_WEIGHTS["required"] * 100,
                "score": required_score,
            },
            {
                "factor": "preferred_skills",
                "weight_percent": JOB_MATCH_WEIGHTS["preferred"] * 100,
                "score": preferred_score,
            },
            {"factor": "role_alignment", "weight_percent": JOB_MATCH_WEIGHTS["role"] * 100, "score": role_score},
            {
                "factor": "preference_alignment",
                "weight_percent": JOB_MATCH_WEIGHTS["preference"] * 100,
                "score": preference_score,
            },
        ]

        strength_values = list(evidence_map.values())
        if strength_values:
            best_strength = max(
                strength_values,
                key=lambda e: {"low": 0, "medium": 1, "high": 2}.get(e.evidence_strength.value, 0),
            )
            evidence_strength = best_strength.evidence_strength.value
        else:
            evidence_strength = "low"

        return {
            "coverage": coverage,
            "has_sufficient_mapping": True,
            "has_user_evidence": True,
            "message": None,
            "required": required_rows,
            "preferred": preferred_rows,
            "why": why,
            "evidence_strength": evidence_strength,
        }

    async def recommended_jobs(
        self,
        user: User,
        *,
        sort: str = "coverage",
        limit: int = 20,
    ) -> list[dict]:
        jobs = (
            await self.db.execute(
                select(Job).where(Job.status == "active").order_by(Job.posted_at.desc().nulls_last()).limit(50)
            )
        ).scalars().all()
        results: list[dict] = []
        for job in jobs:
            match = await self.match_job(user, job.id)
            if not match.get("has_sufficient_mapping"):
                continue
            results.append(
                {
                    "job_id": str(job.id),
                    "slug": job.slug,
                    "title": job.title,
                    "coverage": match.get("coverage"),
                    "has_user_evidence": match.get("has_user_evidence"),
                    "missing_skill_count": sum(
                        1 for r in match.get("required", []) if r["status"] == "missing"
                    ),
                }
            )
        if sort == "coverage":
            results.sort(key=lambda x: (x["coverage"] or 0), reverse=True)
        elif sort == "newest":
            pass
        return results[:limit]
