"""Evening review queue for manual assignment links."""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.manual_assignment import ManualAssignmentReport, ManualAssignmentReview
from app.services.manual_assignment_service import ManualAssignmentService

router = APIRouter(prefix="/admin/assignments")


def _svc(db: AsyncSession = Depends(get_db)) -> ManualAssignmentService:
    return ManualAssignmentService(db)


@router.get("", response_model=list[ManualAssignmentReport])
async def assignment_review_queue(
    _admin: User = Depends(get_current_admin),
    service: ManualAssignmentService = Depends(_svc),
) -> list[ManualAssignmentReport]:
    return [ManualAssignmentReport(**item) for item in await service.review_queue()]


@router.patch("/{submission_id}", response_model=ManualAssignmentReport)
async def save_assignment_review(
    submission_id: UUID,
    payload: ManualAssignmentReview,
    _admin: User = Depends(get_current_admin),
    service: ManualAssignmentService = Depends(_svc),
) -> ManualAssignmentReport:
    report = await service.save_review(submission_id, payload.review_note)
    return ManualAssignmentReport(**report)
