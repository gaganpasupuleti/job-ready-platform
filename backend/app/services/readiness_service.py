"""Role readiness calculations and snapshots."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.job import UserJobPreference
from app.models.readiness import RoleSkillRequirement, UserRoleReadinessSnapshot
from app.models.readiness_enums import EvidenceStrength, RoleSkillImportance
from app.models.tagging import JobRole, Skill
from app.models.user import User
from app.readiness.formulas import (
    IMPORTANCE_WEIGHTS,
    MIN_ROLE_EVIDENCE_ITEMS,
    effective_score,
    evidence_strength_from_signals,
    weighted_average,
)
from app.services.skill_evidence_service import SkillEvidence, SkillEvidenceService


class ReadinessService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.evidence = SkillEvidenceService(db)

    async def _target_role(self, user: User) -> JobRole | None:
        pref = (
            await self.db.execute(
                select(UserJobPreference).where(UserJobPreference.user_id == user.id)
            )
        ).scalar_one_or_none()
        if pref and pref.target_role_id:
            return await self.db.get(JobRole, pref.target_role_id)
        return None

    async def _role_requirements(self, role_id: UUID) -> list[RoleSkillRequirement]:
        return list(
            (
                await self.db.execute(
                    select(RoleSkillRequirement)
                    .where(RoleSkillRequirement.role_id == role_id)
                    .options(selectinload(RoleSkillRequirement.role_id))  # noqa: SIM210
                )
            ).scalars().all()
        )

    async def _requirements_with_skills(self, role_id: UUID) -> list[tuple[RoleSkillRequirement, Skill]]:
        rows = (
            await self.db.execute(
                select(RoleSkillRequirement, Skill)
                .join(Skill, Skill.id == RoleSkillRequirement.skill_id)
                .where(RoleSkillRequirement.role_id == role_id)
            )
        ).all()
        return [(req, skill) for req, skill in rows]

    def _role_readiness_from_requirements(
        self,
        requirements: list[tuple[RoleSkillRequirement, Skill]],
        evidence_map: dict[str, SkillEvidence],
    ) -> dict[str, Any]:
        if not requirements:
            return {
                "score": None,
                "has_minimum_evidence": False,
                "evidence_strength": EvidenceStrength.LOW.value,
                "core_coverage": {"covered": 0, "total": 0},
                "skills": [],
                "strong_skills": [],
                "developing_skills": [],
                "missing_skills": [],
                "why_breakdown": [],
            }

        skill_rows: list[dict[str, Any]] = []
        weighted_items: list[tuple[float, float]] = []
        core_total = 0
        core_covered = 0
        total_activity = 0
        diversities: list[int] = []

        from app.readiness.skill_mapping import normalize_skill_key  # noqa: PLC0415

        for req, skill in requirements:
            ev = evidence_map.get(normalize_skill_key(skill.slug)) or evidence_map.get(
                normalize_skill_key(skill.name)
            )
            readiness = ev.score if ev else 0.0
            strength = ev.evidence_strength if ev else EvidenceStrength.LOW
            eff = effective_score(readiness, strength) if ev else 0.0
            imp = req.importance.value if hasattr(req.importance, "value") else str(req.importance)
            imp_w = IMPORTANCE_WEIGHTS.get(imp, 0.5) * float(req.weight or 1.0)
            if ev:
                weighted_items.append((eff, imp_w))
                total_activity += ev.activity_count
                diversities.append(len(ev.sources))
            status = "missing"
            if readiness >= 80:
                status = "strong"
            elif readiness >= 60:
                status = "developing"
            elif readiness > 0:
                status = "needs_work"
            if imp == RoleSkillImportance.CORE.value:
                core_total += 1
                if readiness >= 60:
                    core_covered += 1
            skill_rows.append(
                {
                    "skill_id": str(skill.id),
                    "skill_name": skill.name,
                    "skill_slug": skill.slug,
                    "importance": imp,
                    "weight": req.weight,
                    "readiness": readiness,
                    "effective_score": eff,
                    "evidence_strength": strength.value,
                    "status": status,
                    "sources": [
                        {"source": s.source, "score": s.score, "activity_count": s.activity_count}
                        for s in (ev.sources if ev else [])
                    ],
                }
            )

        score = weighted_average(weighted_items) if weighted_items else None
        overall_strength = evidence_strength_from_signals(
            total_activity, max(diversities) if diversities else 0
        )
        has_min = total_activity >= MIN_ROLE_EVIDENCE_ITEMS and bool(weighted_items)

        strong = [s["skill_name"] for s in skill_rows if s["status"] == "strong"]
        developing = [s["skill_name"] for s in skill_rows if s["status"] in ("developing", "needs_work")]
        missing = [s["skill_name"] for s in skill_rows if s["status"] == "missing"]

        why = [
            {
                "skill": s["skill_name"],
                "importance": s["importance"],
                "weight_percent": round(s["weight"] * IMPORTANCE_WEIGHTS.get(s["importance"], 0.5) * 100, 1),
                "readiness": s["readiness"],
                "effective_score": s["effective_score"],
                "evidence_strength": s["evidence_strength"],
            }
            for s in skill_rows
        ]

        return {
            "score": round(score, 1) if score is not None and has_min else None,
            "has_minimum_evidence": has_min,
            "evidence_strength": overall_strength.value,
            "core_coverage": {"covered": core_covered, "total": core_total},
            "skills": skill_rows,
            "strong_skills": strong,
            "developing_skills": developing,
            "missing_skills": missing,
            "why_breakdown": why,
        }

    async def get_overview(self, user: User) -> dict[str, Any]:
        role = await self._target_role(user)
        evidence_map = await self.evidence.collect_all(user.id)
        if role is None:
            return {
                "target_role": None,
                "score": None,
                "has_minimum_evidence": False,
                "evidence_strength": EvidenceStrength.LOW.value,
                "core_coverage": {"covered": 0, "total": 0},
                "skills": [],
                "strong_skills": [],
                "developing_skills": [],
                "missing_skills": [],
                "why_breakdown": [],
                "trend": [],
                "message": "Select a target role in Jobs preferences to see role readiness.",
            }
        reqs = await self._requirements_with_skills(role.id)
        result = self._role_readiness_from_requirements(reqs, evidence_map)
        result["target_role"] = {"id": str(role.id), "name": role.name, "slug": role.slug}
        result["trend"] = await self._trend(user.id, role.id)
        result["message"] = None if result["has_minimum_evidence"] else (
            "Not enough evidence yet. Complete MCQs, SQL, projects, or interview practice to build your profile."
        )
        return result

    async def list_skills(self, user: User) -> list[dict[str, Any]]:
        evidence_map = await self.evidence.collect_all(user.id)
        return [
            {
                "skill_id": str(ev.skill_id),
                "skill": ev.skill_name,
                "skill_slug": ev.skill_slug,
                "score": ev.score,
                "effective_score": ev.effective_score,
                "evidence_strength": ev.evidence_strength.value,
                "activity_count": ev.activity_count,
                "last_activity_at": ev.last_activity_at.isoformat() if ev.last_activity_at else None,
                "status": ev.status,
                "sources": [
                    {"source": s.source, "score": s.score, "activity_count": s.activity_count}
                    for s in ev.sources
                ],
            }
            for ev in sorted(evidence_map.values(), key=lambda x: -x.score)
        ]

    async def compare_roles(self, user: User, limit: int = 6) -> list[dict[str, Any]]:
        evidence_map = await self.evidence.collect_all(user.id)
        roles = (await self.db.execute(select(JobRole).limit(limit))).scalars().all()
        out: list[dict[str, Any]] = []
        for role in roles:
            reqs = await self._requirements_with_skills(role.id)
            if not reqs:
                continue
            calc = self._role_readiness_from_requirements(reqs, evidence_map)
            out.append(
                {
                    "role_id": str(role.id),
                    "role_name": role.name,
                    "role_slug": role.slug,
                    "score": calc["score"],
                    "has_minimum_evidence": calc["has_minimum_evidence"],
                }
            )
        return sorted(out, key=lambda x: (x["score"] or 0), reverse=True)

    async def get_role_detail(self, user: User, role_slug: str) -> dict[str, Any]:
        role = (
            await self.db.execute(select(JobRole).where(JobRole.slug == role_slug))
        ).scalar_one_or_none()
        if role is None:
            return {"error": "Role not found"}
        evidence_map = await self.evidence.collect_all(user.id)
        reqs = await self._requirements_with_skills(role.id)
        calc = self._role_readiness_from_requirements(reqs, evidence_map)
        calc["target_role"] = {"id": str(role.id), "name": role.name, "slug": role.slug}
        calc["trend"] = await self._trend(user.id, role.id)
        return calc

    async def refresh_snapshot(self, user: User) -> dict[str, Any]:
        overview = await self.get_overview(user)
        role_data = overview.get("target_role")
        if role_data and overview.get("has_minimum_evidence") and overview.get("score") is not None:
            snap = UserRoleReadinessSnapshot(
                user_id=user.id,
                role_id=UUID(role_data["id"]),
                score=float(overview["score"]),
                evidence_strength=overview["evidence_strength"],
                breakdown_json={
                    "skills": overview["skills"],
                    "core_coverage": overview["core_coverage"],
                },
            )
            self.db.add(snap)
            await self.db.commit()
        return overview

    async def _trend(self, user_id: UUID, role_id: UUID, days: int = 30) -> list[dict[str, Any]]:
        since = datetime.now(UTC) - timedelta(days=days)
        rows = (
            await self.db.execute(
                select(UserRoleReadinessSnapshot)
                .where(
                    UserRoleReadinessSnapshot.user_id == user_id,
                    UserRoleReadinessSnapshot.role_id == role_id,
                    UserRoleReadinessSnapshot.created_at >= since,
                )
                .order_by(UserRoleReadinessSnapshot.created_at.asc())
            )
        ).scalars().all()
        return [
            {"score": r.score, "created_at": r.created_at.isoformat(), "evidence_strength": r.evidence_strength}
            for r in rows
        ]
