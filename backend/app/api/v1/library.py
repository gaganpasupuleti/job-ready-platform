"""Student library. Listing and opening a book does not write a reading record."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.library import ReadLink, ReadingProgressUpdate, ReadingStatusUpdate, StudentLibraryBook, StudentLibraryPage
from app.services.library_service import LibraryService

router = APIRouter(prefix="/library")


def _svc(db: AsyncSession = Depends(get_db)) -> LibraryService:
    return LibraryService(db)


@router.get("/books", response_model=StudentLibraryPage)
async def browse_books(
    q: str | None = Query(default=None, max_length=200),
    category: str | None = Query(default=None, max_length=80),
    current_user: User = Depends(get_current_user),
    svc: LibraryService = Depends(_svc),
) -> StudentLibraryPage:
    return await svc.browse(current_user, q, category)


@router.get("/saved", response_model=list[StudentLibraryBook])
async def saved_books(
    current_user: User = Depends(get_current_user),
    svc: LibraryService = Depends(_svc),
) -> list[StudentLibraryBook]:
    return await svc.saved(current_user)


@router.get("/books/{book_id}", response_model=StudentLibraryBook)
async def get_book(
    book_id: UUID,
    current_user: User = Depends(get_current_user),
    svc: LibraryService = Depends(_svc),
) -> StudentLibraryBook:
    return await svc.student_get(current_user, book_id)


@router.post("/books/{book_id}/bookmark", response_model=StudentLibraryBook)
async def bookmark_book(
    book_id: UUID,
    current_user: User = Depends(get_current_user),
    svc: LibraryService = Depends(_svc),
) -> StudentLibraryBook:
    return await svc.bookmark(current_user, book_id)


@router.delete("/books/{book_id}/bookmark", response_model=StudentLibraryBook)
async def unbookmark_book(
    book_id: UUID,
    current_user: User = Depends(get_current_user),
    svc: LibraryService = Depends(_svc),
) -> StudentLibraryBook:
    return await svc.unbookmark(current_user, book_id)


@router.put("/books/{book_id}/reading-status", response_model=StudentLibraryBook)
async def set_reading_status(
    book_id: UUID,
    payload: ReadingStatusUpdate,
    current_user: User = Depends(get_current_user),
    svc: LibraryService = Depends(_svc),
) -> StudentLibraryBook:
    return await svc.set_reading_status(current_user, book_id, payload.status)


@router.put("/books/{book_id}/progress", response_model=StudentLibraryBook)
async def set_progress(
    book_id: UUID,
    payload: ReadingProgressUpdate,
    current_user: User = Depends(get_current_user),
    svc: LibraryService = Depends(_svc),
) -> StudentLibraryBook:
    return await svc.set_progress(current_user, book_id, payload.last_page)


@router.get("/books/{book_id}/read-link", response_model=ReadLink)
async def read_link(
    book_id: UUID,
    current_user: User = Depends(get_current_user),
    svc: LibraryService = Depends(_svc),
) -> ReadLink:
    return await svc.read_link(current_user, book_id)


@router.get("/books/{book_id}/file")
async def read_file(
    book_id: UUID,
    current_user: User = Depends(get_current_user),
    svc: LibraryService = Depends(_svc),
) -> Response:
    payload = await svc.file_bytes(current_user, book_id)
    return Response(content=payload, media_type="application/pdf")
