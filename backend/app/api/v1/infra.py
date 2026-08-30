"""Student Cloud / DevOps / Cybersecurity dashboards and scenarios."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.scenario import ScenarioSubmitRequest
from app.services.scenario_service import ScenarioService

router = APIRouter()


@router.get("/cloud")
async def cloud_home(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await ScenarioService(db).domain_home(user, "cloud")


@router.get("/cloud/progress")
async def cloud_progress(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await ScenarioService(db).domain_progress(user, "cloud")


@router.get("/devops")
async def devops_home(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await ScenarioService(db).domain_home(user, "devops")


@router.get("/devops/progress")
async def devops_progress(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await ScenarioService(db).domain_progress(user, "devops")


@router.get("/cybersecurity")
async def cyber_home(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await ScenarioService(db).domain_home(user, "cybersecurity")


@router.get("/cybersecurity/progress")
async def cyber_progress(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await ScenarioService(db).domain_progress(user, "cybersecurity")


@router.get("/scenarios")
async def list_scenarios(
    domain: str | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await ScenarioService(db).list_challenges(user, domain=domain)


@router.get("/scenarios/{slug}")
async def get_scenario(
    slug: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await ScenarioService(db).get_challenge(slug, user)


@router.post("/scenarios/{slug}/submit")
async def submit_scenario(
    slug: str,
    body: ScenarioSubmitRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await ScenarioService(db).submit(slug, user, body.answers)


@router.get("/scenario-submissions/{submission_id}")
async def get_scenario_submission(
    submission_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await ScenarioService(db).get_submission(submission_id, user)
