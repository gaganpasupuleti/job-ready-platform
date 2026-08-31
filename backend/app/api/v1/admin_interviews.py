from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.interview import InterviewPackPublic
from app.schemas.interview_session import AdminInterviewPackCreate, AdminInterviewPackUpdate
from app.services.admin_interview_service import AdminInterviewPackService

router = APIRouter(prefix="/admin/interviews")


@router.get("/packs", response_model=list[InterviewPackPublic])
async def admin_list_packs(
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> list[InterviewPackPublic]:
    return await AdminInterviewPackService(db).list_packs()


@router.post("/packs", response_model=InterviewPackPublic)
async def admin_create_pack(
    payload: AdminInterviewPackCreate,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> InterviewPackPublic:
    return await AdminInterviewPackService(db).create(payload)


@router.patch("/packs/{pack_id}", response_model=InterviewPackPublic)
async def admin_update_pack(
    pack_id: UUID,
    payload: AdminInterviewPackUpdate,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> InterviewPackPublic:
    return await AdminInterviewPackService(db).update(pack_id, payload)
