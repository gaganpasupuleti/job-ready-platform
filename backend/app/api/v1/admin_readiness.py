"""Admin readiness configuration — role skill requirements."""

from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_admin
from app.core.exceptions import AppException
from app.db.session import get_db
from app.models.readiness import RoleSkillRequirement
from app.models.readiness_enums import RoleSkillImportance, RoleSkillSource
from app.models.tagging import JobRole, Skill
from app.models.user import User

router = APIRouter(prefix="/admin/readiness")


class RoleSkillRequirementIn(BaseModel):
    skill_id: UUID
    importance: RoleSkillImportance
    weight: float = Field(ge=0, le=10)
    minimum_readiness: float | None = Field(default=None, ge=0, le=100)


class RoleSkillRequirementOut(BaseModel):
    id: UUID
    role_id: UUID
    skill_id: UUID
    skill_name: str
    importance: RoleSkillImportance
    weight: float
    minimum_readiness: float | None
    source: RoleSkillSource


@router.get("/roles")
async def list_roles_with_requirements(
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    roles = (await db.execute(select(JobRole).order_by(JobRole.name))).scalars().all()
    out = []
    for role in roles:
        reqs = (
            await db.execute(
                select(RoleSkillRequirement, Skill)
                .join(Skill, Skill.id == RoleSkillRequirement.skill_id)
                .where(RoleSkillRequirement.role_id == role.id)
            )
        ).all()
        out.append(
            {
                "role": {"id": str(role.id), "name": role.name, "slug": role.slug},
                "requirements": [
                    {
                        "id": str(r.id),
                        "skill_id": str(s.id),
                        "skill_name": s.name,
                        "importance": r.importance.value,
                        "weight": r.weight,
                        "minimum_readiness": r.minimum_readiness,
                        "source": r.source.value,
                    }
                    for r, s in reqs
                ],
            }
        )
    return out


@router.put("/roles/{role_id}/requirements/{skill_id}")
async def upsert_requirement(
    role_id: UUID,
    skill_id: UUID,
    payload: RoleSkillRequirementIn,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    if payload.skill_id != skill_id:
        raise AppException("skill_id mismatch", status_code=400)
    existing = (
        await db.execute(
            select(RoleSkillRequirement).where(
                RoleSkillRequirement.role_id == role_id,
                RoleSkillRequirement.skill_id == skill_id,
            )
        )
    ).scalar_one_or_none()
    if existing:
        existing.importance = payload.importance
        existing.weight = payload.weight
        existing.minimum_readiness = payload.minimum_readiness
        existing.source = RoleSkillSource.MANUAL
    else:
        existing = RoleSkillRequirement(
            role_id=role_id,
            skill_id=skill_id,
            importance=payload.importance,
            weight=payload.weight,
            minimum_readiness=payload.minimum_readiness,
            source=RoleSkillSource.MANUAL,
        )
        db.add(existing)
    await db.commit()
    skill = await db.get(Skill, skill_id)
    return {
        "id": str(existing.id),
        "skill_name": skill.name if skill else "",
        "importance": existing.importance.value,
        "weight": existing.weight,
    }


@router.delete("/roles/{role_id}/requirements/{skill_id}", status_code=204)
async def delete_requirement(
    role_id: UUID,
    skill_id: UUID,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> None:
    row = (
        await db.execute(
            select(RoleSkillRequirement).where(
                RoleSkillRequirement.role_id == role_id,
                RoleSkillRequirement.skill_id == skill_id,
            )
        )
    ).scalar_one_or_none()
    if row:
        await db.delete(row)
        await db.commit()
