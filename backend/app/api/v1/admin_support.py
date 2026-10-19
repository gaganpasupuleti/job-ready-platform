"""Admin and trainer review queue for student feedback."""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_admin
from app.core.exceptions import AppException
from app.db.session import get_db
from app.models.support_ticket import TICKET_CATEGORIES, TICKET_STATUSES
from app.models.user import User
from app.schemas.support_ticket import (
    AdminSupportTicketDetail,
    AdminSupportTicketSummary,
    SupportReplyCreate,
    SupportStatusUpdate,
)
from app.services.support_ticket_service import SupportTicketService

router = APIRouter(prefix="/admin/support")


def _svc(db: AsyncSession = Depends(get_db)) -> SupportTicketService:
    return SupportTicketService(db)


@router.get("/tickets", response_model=list[AdminSupportTicketSummary])
async def list_feedback_tickets(
    category: str | None = Query(default=None),
    status: str | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    _admin: User = Depends(get_current_admin),
    service: SupportTicketService = Depends(_svc),
) -> list[AdminSupportTicketSummary]:
    if category is not None and category not in TICKET_CATEGORIES:
        raise AppException("Unknown category", status_code=422)
    if status is not None and status not in TICKET_STATUSES:
        raise AppException("Unknown status", status_code=422)
    return await service.admin_list(category=category, status=status, date_from=date_from, date_to=date_to)


@router.get("/tickets/{ticket_id}", response_model=AdminSupportTicketDetail)
async def get_feedback_ticket(
    ticket_id: UUID,
    _admin: User = Depends(get_current_admin),
    service: SupportTicketService = Depends(_svc),
) -> AdminSupportTicketDetail:
    return await service.admin_detail(ticket_id)


@router.post("/tickets/{ticket_id}/replies", response_model=AdminSupportTicketDetail)
async def reply_to_feedback_ticket(
    ticket_id: UUID,
    payload: SupportReplyCreate,
    admin: User = Depends(get_current_admin),
    service: SupportTicketService = Depends(_svc),
) -> AdminSupportTicketDetail:
    return await service.add_admin_reply(admin, ticket_id, payload)


@router.patch("/tickets/{ticket_id}", response_model=AdminSupportTicketDetail)
async def update_feedback_status(
    ticket_id: UUID,
    payload: SupportStatusUpdate,
    admin: User = Depends(get_current_admin),
    service: SupportTicketService = Depends(_svc),
) -> AdminSupportTicketDetail:
    return await service.change_status(admin, ticket_id, payload)
