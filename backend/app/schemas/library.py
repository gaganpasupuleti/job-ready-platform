from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

BookStatus = Literal["draft", "published", "archived"]
ReadingStatus = Literal["not_started", "reading", "completed"]


class LibraryBookWrite(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    author: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=4000)
    category: str = Field(min_length=1, max_length=80)
    external_url: str = Field(min_length=8, max_length=2000)
    status: BookStatus = "draft"


class LibraryBookPatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    author: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    category: str | None = Field(default=None, min_length=1, max_length=80)
    external_url: str | None = Field(default=None, min_length=8, max_length=2000)
    status: BookStatus | None = None


class AdminLibraryBook(BaseModel):
    id: UUID
    title: str
    author: str
    description: str
    category: str
    external_url: str
    status: BookStatus


class StudentLibraryBook(BaseModel):
    id: UUID
    title: str
    author: str
    description: str
    category: str
    available: bool
    external_url: str | None = None
    bookmarked: bool
    reading_status: ReadingStatus | None = None


class StudentLibraryPage(BaseModel):
    items: list[StudentLibraryBook]
    categories: list[str]


class ReadingStatusUpdate(BaseModel):
    status: ReadingStatus
