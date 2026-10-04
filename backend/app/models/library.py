"""Library books. Opening a row does not record reading or a page."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.base import UUIDPrimaryKeyMixin


class LibraryBook(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "library_books"

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    author: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(String(4000), nullable=False, default="")
    category: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    external_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    storage_key: Mapped[str | None] = mapped_column(String(400), nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class LibraryBookmark(Base):
    __tablename__ = "library_bookmarks"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    book_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("library_books.id", ondelete="CASCADE"),
        primary_key=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class LibraryReadingStatus(Base):
    __tablename__ = "library_reading_statuses"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    book_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("library_books.id", ondelete="CASCADE"),
        primary_key=True,
    )
    status: Mapped[str | None] = mapped_column(String(16), nullable=True)
    last_page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
