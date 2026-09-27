"""Library metadata. This service never requests the external URL."""

from urllib.parse import urlparse
from uuid import UUID, uuid4

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.library import LibraryBook, LibraryBookmark, LibraryReadingStatus
from app.models.user import User
from app.schemas.library import (
    AdminLibraryBook,
    LibraryBookPatch,
    LibraryBookWrite,
    StudentLibraryBook,
    StudentLibraryPage,
)

BOOK_STATUSES = {"draft", "published", "archived"}
READING_STATUSES = {"not_started", "reading", "completed"}


def require_https_url(value: str) -> str:
    raw = value.strip()
    if not raw or any(character.isspace() for character in raw) or "\\" in raw:
        raise AppException("Enter one https URL without spaces.", status_code=422)
    if len(raw) > 2000:
        raise AppException("The URL is too long.", status_code=422)
    parsed = urlparse(raw)
    if parsed.scheme.lower() != "https" or not parsed.hostname:
        raise AppException("Only https links are allowed.", status_code=422)
    if parsed.username or parsed.password:
        raise AppException("The URL cannot include a username or password.", status_code=422)
    return "https" + raw[len(parsed.scheme) :]


def _clean_text(value: str, label: str, limit: int) -> str:
    text = value.strip()
    if not text:
        raise AppException(f"Enter a {label}.", status_code=422)
    if len(text) > limit:
        raise AppException(f"The {label} is too long.", status_code=422)
    return text


class LibraryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_book(self, admin: User, payload: LibraryBookWrite) -> AdminLibraryBook:
        book = LibraryBook(
            id=uuid4(),
            title=_clean_text(payload.title, "title", 200),
            author=_clean_text(payload.author, "author", 200),
            description=payload.description.strip(),
            category=_clean_text(payload.category, "category", 80),
            external_url=require_https_url(payload.external_url),
            status=payload.status,
            created_by=admin.id,
        )
        self.db.add(book)
        await self.db.commit()
        return self._admin(book)

    async def update_book(self, book_id: UUID, payload: LibraryBookPatch) -> AdminLibraryBook:
        book = await self._book(book_id)
        changes = payload.model_dump(exclude_unset=True)
        if "title" in changes:
            book.title = _clean_text(changes["title"], "title", 200)
        if "author" in changes:
            book.author = _clean_text(changes["author"], "author", 200)
        if "description" in changes:
            book.description = changes["description"].strip()
        if "category" in changes:
            book.category = _clean_text(changes["category"], "category", 80)
        if "external_url" in changes:
            book.external_url = require_https_url(changes["external_url"])
        if "status" in changes:
            if changes["status"] not in BOOK_STATUSES:
                raise AppException("Choose draft, published, or archived.", status_code=422)
            book.status = changes["status"]
        await self.db.commit()
        return self._admin(book)

    async def admin_list(self) -> list[AdminLibraryBook]:
        rows = (
            await self.db.execute(select(LibraryBook).order_by(LibraryBook.updated_at.desc(), LibraryBook.title))
        ).scalars()
        return [self._admin(book) for book in rows]

    async def admin_get(self, book_id: UUID) -> AdminLibraryBook:
        return self._admin(await self._book(book_id))

    async def browse(self, user: User, query: str | None, category: str | None) -> StudentLibraryPage:
        statement = select(LibraryBook).where(LibraryBook.status == "published")
        if category and category.strip():
            statement = statement.where(LibraryBook.category == category.strip())
        if query and query.strip():
            needle = f"%{query.strip()}%"
            statement = statement.where(
                or_(LibraryBook.title.ilike(needle), LibraryBook.author.ilike(needle))
            )
        books = (
            await self.db.execute(statement.order_by(LibraryBook.title, LibraryBook.id))
        ).scalars().all()
        categories = (
            await self.db.execute(
                select(LibraryBook.category)
                .where(LibraryBook.status == "published")
                .distinct()
                .order_by(LibraryBook.category)
            )
        ).scalars().all()
        return StudentLibraryPage(
            items=[await self._student(book, user.id) for book in books],
            categories=list(categories),
        )

    async def saved(self, user: User) -> list[StudentLibraryBook]:
        book_ids = set(
            (
                await self.db.execute(
                    select(LibraryBookmark.book_id).where(LibraryBookmark.user_id == user.id)
                )
            ).scalars()
        )
        book_ids.update(
            (
                await self.db.execute(
                    select(LibraryReadingStatus.book_id).where(LibraryReadingStatus.user_id == user.id)
                )
            ).scalars()
        )
        if not book_ids:
            return []
        books = (
            await self.db.execute(
                select(LibraryBook).where(LibraryBook.id.in_(book_ids)).order_by(LibraryBook.title)
            )
        ).scalars()
        return [await self._student(book, user.id) for book in books]

    async def student_get(self, user: User, book_id: UUID) -> StudentLibraryBook:
        book = await self._book(book_id)
        if book.status != "published" and not await self._has_personal_record(user.id, book.id):
            raise AppException("Book not found", status_code=404)
        return await self._student(book, user.id)

    async def bookmark(self, user: User, book_id: UUID) -> StudentLibraryBook:
        book = await self._published(book_id)
        existing = await self.db.get(LibraryBookmark, {"user_id": user.id, "book_id": book.id})
        if existing is None:
            self.db.add(LibraryBookmark(user_id=user.id, book_id=book.id))
            try:
                await self.db.commit()
            except IntegrityError:
                await self.db.rollback()
        return await self._student(book, user.id)

    async def unbookmark(self, user: User, book_id: UUID) -> StudentLibraryBook:
        book = await self._book(book_id)
        if book.status == "draft":
            raise AppException("Book not found", status_code=404)
        personal = await self._has_personal_record(user.id, book.id)
        if book.status != "published" and not personal:
            raise AppException("Book not found", status_code=404)
        row = await self.db.get(LibraryBookmark, {"user_id": user.id, "book_id": book.id})
        if row is not None:
            await self.db.delete(row)
            await self.db.commit()
        return await self._student(book, user.id)

    async def set_reading_status(self, user: User, book_id: UUID, status: str) -> StudentLibraryBook:
        if status not in READING_STATUSES:
            raise AppException("Choose not started, reading, or completed.", status_code=422)
        book = await self._published(book_id)
        row = await self.db.get(LibraryReadingStatus, {"user_id": user.id, "book_id": book.id})
        if row is None:
            self.db.add(LibraryReadingStatus(user_id=user.id, book_id=book.id, status=status))
        else:
            row.status = status
        await self.db.commit()
        return await self._student(book, user.id)

    async def _published(self, book_id: UUID) -> LibraryBook:
        book = await self._book(book_id)
        if book.status != "published":
            raise AppException("This resource is not available.", status_code=404)
        return book

    async def _book(self, book_id: UUID) -> LibraryBook:
        book = await self.db.get(LibraryBook, book_id)
        if book is None:
            raise AppException("Book not found", status_code=404)
        return book

    async def _has_personal_record(self, user_id: UUID, book_id: UUID) -> bool:
        bookmark = await self.db.get(LibraryBookmark, {"user_id": user_id, "book_id": book_id})
        if bookmark is not None:
            return True
        status = await self.db.get(LibraryReadingStatus, {"user_id": user_id, "book_id": book_id})
        return status is not None

    async def _student(self, book: LibraryBook, user_id: UUID) -> StudentLibraryBook:
        bookmark = await self.db.get(LibraryBookmark, {"user_id": user_id, "book_id": book.id})
        status = await self.db.get(LibraryReadingStatus, {"user_id": user_id, "book_id": book.id})
        published = book.status == "published"
        return StudentLibraryBook(
            id=book.id,
            title=book.title,
            author=book.author,
            description=book.description,
            category=book.category,
            available=published,
            external_url=book.external_url if published else None,
            bookmarked=bookmark is not None,
            reading_status=status.status if status is not None else None,
        )

    @staticmethod
    def _admin(book: LibraryBook) -> AdminLibraryBook:
        return AdminLibraryBook(
            id=book.id,
            title=book.title,
            author=book.author,
            description=book.description,
            category=book.category,
            external_url=book.external_url,
            status=book.status,  # type: ignore[arg-type]
        )
