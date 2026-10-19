from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class NotificationItem(BaseModel):
    id: UUID
    event_type: str
    message: str
    destination_path: str
    created_at: datetime
    read_at: datetime | None = None


class NotificationPage(BaseModel):
    items: list[NotificationItem]
    next_cursor: str | None = None


class UnreadCount(BaseModel):
    count: int = Field(ge=0)
