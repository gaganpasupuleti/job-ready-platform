"""Student-owned feedback tickets."""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.support_ticket import (
    SupportReplyCreate,
    SupportTicketCreate,
    SupportTicketDetail,
    SupportTicketSummary,
)
from app.services.support_ticket_service import SupportTicketService

router = APIRouter(prefix="/support")


def _svc(db: AsyncSession = Depends(get_db)) -> SupportTicketService:
    return SupportTicketService(db)


@router.get("/tickets", response_model=list[SupportTicketSummary])
async def list_my_tickets(
    user: User = Depends(get_current_user),
    service: SupportTicketService = Depends(_svc),
) -> list[SupportTicketSummary]:
    return await service.list_for_student(user)


@router.post("/tickets", response_model=SupportTicketDetail)
async def create_ticket(
    payload: SupportTicketCreate,
    user: User = Depends(get_current_user),
    service: SupportTicketService = Depends(_svc),
) -> SupportTicketDetail:
    return await service.create_ticket(user, payload)


@router.get("/tickets/{ticket_id}", response_model=SupportTicketDetail)
async def get_my_ticket(
    ticket_id: UUID,
    user: User = Depends(get_current_user),
    service: SupportTicketService = Depends(_svc),
) -> SupportTicketDetail:
    return await service.student_detail(user, ticket_id)


@router.post("/tickets/{ticket_id}/replies", response_model=SupportTicketDetail)
async def reply_to_my_ticket(
    ticket_id: UUID,
    payload: SupportReplyCreate,
    user: User = Depends(get_current_user),
    service: SupportTicketService = Depends(_svc),
) -> SupportTicketDetail:
    return await service.add_student_reply(user, ticket_id, payload)
