"""Student AI practice and prompt-challenge APIs."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.prompt import PromptEvaluateRequest
from app.services.prompt_service import PromptService

router = APIRouter(prefix="/ai")


@router.get("/home")
async def ai_home(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await PromptService(db).ai_home(current_user)


@router.get("/progress")
async def ai_progress(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await PromptService(db).ai_progress(current_user)


@router.get("/prompts")
async def list_prompt_challenges(
    difficulty: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await PromptService(db).list_challenges(current_user, difficulty=difficulty)


@router.get("/prompts/{slug}")
async def get_prompt_challenge(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await PromptService(db).get_challenge(slug, current_user)


@router.post("/prompts/{slug}/test")
async def test_prompt(
    slug: str,
    body: PromptEvaluateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await PromptService(db).evaluate(slug, current_user, body.prompt_text, is_test=True)


@router.post("/prompts/{slug}/submit")
async def submit_prompt(
    slug: str,
    body: PromptEvaluateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await PromptService(db).evaluate(slug, current_user, body.prompt_text, is_test=False)


@router.get("/prompt-submissions")
async def list_prompt_submissions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await PromptService(db).list_submissions(current_user)


@router.get("/prompt-submissions/{submission_id}")
async def get_prompt_submission(
    submission_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await PromptService(db).get_submission(submission_id, current_user)


@router.post("/prompts/{challenge_id}/bookmark")
async def bookmark_prompt(
    challenge_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await PromptService(db).toggle_bookmark(challenge_id, current_user)


@router.get("/prompt-bookmarks")
async def prompt_bookmarks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await PromptService(db).list_bookmarks(current_user)
