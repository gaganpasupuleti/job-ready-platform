"""Admin APIs for AI coverage and prompt challenges."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Body, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.prompt import PromptChallengeAdminIn
from app.services.prompt_service import PromptAdminService

router = APIRouter(prefix="/admin/ai")


@router.get("")
async def admin_ai_home(
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    return await PromptAdminService(db).coverage()


@router.get("/prompts")
async def list_admin_prompts(
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    return await PromptAdminService(db).list_challenges()


@router.get("/prompts/{challenge_id}")
async def get_admin_prompt(
    challenge_id: UUID,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    return await PromptAdminService(db).get_challenge(challenge_id)


@router.post("/prompts")
async def create_admin_prompt(
    body: PromptChallengeAdminIn,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    return await PromptAdminService(db).create_challenge(body, admin)


@router.patch("/prompts/{challenge_id}")
async def update_admin_prompt(
    challenge_id: UUID,
    body: dict[str, Any] = Body(...),
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    return await PromptAdminService(db).update_challenge(challenge_id, body)


@router.post("/prompts/{challenge_id}/validate")
async def validate_admin_prompt(
    challenge_id: UUID,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    return await PromptAdminService(db).validate_only(challenge_id)
