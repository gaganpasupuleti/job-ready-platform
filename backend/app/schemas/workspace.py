from uuid import UUID

from pydantic import BaseModel, Field


class WorkspaceNavItem(BaseModel):
    id: UUID
    slug: str
    title: str
    status: str | None = None
    href: str


class WorkspaceNavigation(BaseModel):
    previous: WorkspaceNavItem | None = None
    next: WorkspaceNavItem | None = None
    position: int = 1
    total: int = 0
    items: list[WorkspaceNavItem] = Field(default_factory=list)
