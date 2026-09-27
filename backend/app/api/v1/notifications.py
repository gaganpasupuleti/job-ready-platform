"""Recipient-owned in-app notifications."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.notification import NotificationItem, NotificationPage, UnreadCount
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications")


def _svc(db: AsyncSession = Depends(get_db)) -> NotificationService:
    return NotificationService(db)


@router.get("", response_model=NotificationPage)
async def list_notifications(
    limit: int = Query(default=20, ge=1, le=30),
    cursor: str | None = None,
    user: User = Depends(get_current_user),
    service: NotificationService = Depends(_svc),
) -> NotificationPage:
    return await service.list_for_user(user, limit=limit, cursor=cursor)


@router.get("/unread-count", response_model=UnreadCount)
async def unread_notification_count(
    user: User = Depends(get_current_user),
    service: NotificationService = Depends(_svc),
) -> UnreadCount:
    return await service.unread_count(user)


@router.post("/read-all", response_model=UnreadCount)
async def mark_all_notifications_read(
    user: User = Depends(get_current_user),
    service: NotificationService = Depends(_svc),
) -> UnreadCount:
    return await service.mark_all_read(user)


@router.post("/{notification_id}/read", response_model=NotificationItem)
async def mark_notification_read(
    notification_id: UUID,
    user: User = Depends(get_current_user),
    service: NotificationService = Depends(_svc),
) -> NotificationItem:
    return await service.mark_read(user, notification_id)
