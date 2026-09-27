"""Admin library metadata. Students cannot use these routes."""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.library import AdminLibraryBook, LibraryBookPatch, LibraryBookWrite
from app.services.library_service import LibraryService

router = APIRouter(prefix="/admin/library")


def _svc(db: AsyncSession = Depends(get_db)) -> LibraryService:
    return LibraryService(db)


@router.get("/books", response_model=list[AdminLibraryBook])
async def list_books(
    _admin: User = Depends(get_current_admin),
    svc: LibraryService = Depends(_svc),
) -> list[AdminLibraryBook]:
    return await svc.admin_list()


@router.post("/books", response_model=AdminLibraryBook, status_code=201)
async def create_book(
    payload: LibraryBookWrite,
    admin: User = Depends(get_current_admin),
    svc: LibraryService = Depends(_svc),
) -> AdminLibraryBook:
    return await svc.create_book(admin, payload)


@router.get("/books/{book_id}", response_model=AdminLibraryBook)
async def get_book(
    book_id: UUID,
    _admin: User = Depends(get_current_admin),
    svc: LibraryService = Depends(_svc),
) -> AdminLibraryBook:
    return await svc.admin_get(book_id)


@router.patch("/books/{book_id}", response_model=AdminLibraryBook)
async def update_book(
    book_id: UUID,
    payload: LibraryBookPatch,
    _admin: User = Depends(get_current_admin),
    svc: LibraryService = Depends(_svc),
) -> AdminLibraryBook:
    return await svc.update_book(book_id, payload)
