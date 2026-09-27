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
    external_url: str | None = Field(default=None, max_length=2000)
    storage_key: str | None = Field(default=None, max_length=400)
    status: BookStatus = "draft"


class LibraryBookPatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    author: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    category: str | None = Field(default=None, min_length=1, max_length=80)
    external_url: str | None = Field(default=None, max_length=2000)
    storage_key: str | None = Field(default=None, max_length=400)
    status: BookStatus | None = None


class AdminLibraryBook(BaseModel):
    id: UUID
    title: str
    author: str
    description: str
    category: str
    external_url: str | None = None
    storage_key: str | None = None
    status: BookStatus


class StudentLibraryBook(BaseModel):
    id: UUID
    title: str
    author: str
    description: str
    category: str
    available: bool
    has_file: bool
    external_url: str | None = None
    bookmarked: bool
    reading_status: ReadingStatus | None = None
    last_page: int | None = None


class StudentLibraryPage(BaseModel):
    items: list[StudentLibraryBook]
    categories: list[str]


class ReadingStatusUpdate(BaseModel):
    status: ReadingStatus


class ReadingProgressUpdate(BaseModel):
    last_page: int = Field(ge=1, le=10000)


class ReadLink(BaseModel):
    url: str
    expires_in: int
