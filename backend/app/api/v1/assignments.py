"""Student manual assignment submissions."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.manual_assignment import ManualAssignmentCreate, ManualAssignmentReport
from app.services.manual_assignment_service import ManualAssignmentService

router = APIRouter(prefix="/assignments")


def _svc(db: AsyncSession = Depends(get_db)) -> ManualAssignmentService:
    return ManualAssignmentService(db)


@router.get("", response_model=list[ManualAssignmentReport])
async def list_my_assignments(
    user: User = Depends(get_current_user),
    service: ManualAssignmentService = Depends(_svc),
) -> list[ManualAssignmentReport]:
    return [ManualAssignmentReport(**item) for item in await service.list_for_user(user)]


@router.post("", response_model=ManualAssignmentReport, status_code=201)
async def submit_assignment(
    payload: ManualAssignmentCreate,
    user: User = Depends(get_current_user),
    service: ManualAssignmentService = Depends(_svc),
) -> ManualAssignmentReport:
    report = await service.submit(
        user,
        title=payload.title,
        link=payload.link,
        note=payload.note,
        question=payload.question,
        project_id=payload.project_id,
    )
    return ManualAssignmentReport(**report)
