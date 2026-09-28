from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

BookStatus = Literal["draft", "published", "archived"]
ReadingStatus = Literal["not_started", "reading", "completed"]


def _reject_client_storage_key(data: object) -> object:
    if isinstance(data, dict) and data.get("storage_key"):
        raise ValueError("Upload a PDF. Do not send an object key.")
    if isinstance(data, dict):
        return {key: value for key, value in data.items() if key != "storage_key"}
    return data


class LibraryBookWrite(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    author: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=4000)
    category: str = Field(min_length=1, max_length=80)
    external_url: str | None = Field(default=None, max_length=2000)
    status: BookStatus = "draft"

    @model_validator(mode="before")
    @classmethod
    def reject_storage_key(cls, data: object) -> object:
        return _reject_client_storage_key(data)


class LibraryBookPatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    author: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    category: str | None = Field(default=None, min_length=1, max_length=80)
    external_url: str | None = Field(default=None, max_length=2000)
    status: BookStatus | None = None

    @model_validator(mode="before")
    @classmethod
    def reject_storage_key(cls, data: object) -> object:
        return _reject_client_storage_key(data)


class AdminLibraryBook(BaseModel):
    id: UUID
    title: str
    author: str
    description: str
    category: str
    external_url: str | None = None
    has_file: bool = False
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
