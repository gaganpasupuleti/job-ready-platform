"""Admin coverage and scenario authoring."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Body, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.scenario import ScenarioAdminIn
from app.services.scenario_service import ScenarioAdminService

router = APIRouter(prefix="/admin")


@router.get("/cloud")
async def admin_cloud(_admin: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    data = await ScenarioAdminService(db).coverage("cloud")
    return data.get("cloud") or {}


@router.get("/devops")
async def admin_devops(_admin: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    data = await ScenarioAdminService(db).coverage("devops")
    return data.get("devops") or {}


@router.get("/cybersecurity")
async def admin_cyber(_admin: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    data = await ScenarioAdminService(db).coverage("cybersecurity")
    return data.get("cybersecurity") or {}


@router.get("/scenarios")
async def list_admin_scenarios(_admin: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    return await ScenarioAdminService(db).list_challenges()


@router.get("/scenarios/{challenge_id}")
async def get_admin_scenario(
    challenge_id: UUID,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    return await ScenarioAdminService(db).get_challenge(challenge_id)


@router.post("/scenarios")
async def create_admin_scenario(
    body: ScenarioAdminIn,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    return await ScenarioAdminService(db).create_challenge(body, admin)


@router.patch("/scenarios/{challenge_id}")
async def update_admin_scenario(
    challenge_id: UUID,
    body: dict[str, Any] = Body(...),
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    return await ScenarioAdminService(db).update_challenge(challenge_id, body)
