"""Readiness and skill profile API."""

from fastapi import APIRouter, Depends

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.readiness import (
    ReadinessOverview,
    RoleComparisonItem,
    SkillProfileItem,
)
from app.services.readiness_service import ReadinessService
from app.services.recommendation_service import RecommendationService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/readiness")


def _readiness(db: AsyncSession = Depends(get_db)) -> ReadinessService:
    return ReadinessService(db)


def _recs(db: AsyncSession = Depends(get_db)) -> RecommendationService:
    return RecommendationService(db)


@router.get("", response_model=ReadinessOverview)
async def get_readiness(
    user: User = Depends(get_current_user),
    service: ReadinessService = Depends(_readiness),
    recs: RecommendationService = Depends(_recs),
) -> ReadinessOverview:
    overview = await service.get_overview(user)
    overview["recommended_actions"] = await recs.get_recommendations(user, limit=5)
    return ReadinessOverview(**overview)


@router.get("/skills", response_model=list[SkillProfileItem])
async def list_skills(
    user: User = Depends(get_current_user),
    service: ReadinessService = Depends(_readiness),
) -> list[SkillProfileItem]:
    items = await service.list_skills(user)
    return [SkillProfileItem(**i) for i in items]


@router.get("/roles", response_model=list[RoleComparisonItem])
async def compare_roles(
    user: User = Depends(get_current_user),
    service: ReadinessService = Depends(_readiness),
) -> list[RoleComparisonItem]:
    items = await service.compare_roles(user)
    return [RoleComparisonItem(**i) for i in items]


@router.get("/roles/{role_slug}")
async def role_detail(
    role_slug: str,
    user: User = Depends(get_current_user),
    service: ReadinessService = Depends(_readiness),
):
    return await service.get_role_detail(user, role_slug)


@router.post("/refresh", response_model=ReadinessOverview)
async def refresh_readiness(
    user: User = Depends(get_current_user),
    service: ReadinessService = Depends(_readiness),
    recs: RecommendationService = Depends(_recs),
) -> ReadinessOverview:
    overview = await service.refresh_snapshot(user)
    overview["recommended_actions"] = await recs.get_recommendations(user, limit=5)
    return ReadinessOverview(**overview)


@router.get("/recommendations")
async def recommendations(
    user: User = Depends(get_current_user),
    recs: RecommendationService = Depends(_recs),
):
    return await recs.get_recommendations(user)
