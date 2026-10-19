"""Remove duplicate published library rows (same title). Keeps the best copy per title.

Usage:
  python scripts/library_dedupe_catalog.py --dry-run
  python scripts/library_dedupe_catalog.py
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from collections import defaultdict
from pathlib import Path
from uuid import UUID

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import delete, select

from app.db.session import AsyncSessionLocal
from app.models.library import LibraryBook, LibraryBookmark, LibraryReadingStatus


def _title_key(title: str) -> str:
    return title.strip().lower()


_REMOVED_TITLES = {
    "codequest ownership and license",
}


def _score(book: LibraryBook) -> int:
    key = (book.storage_key or "").lower()
    score = 0
    if book.status == "published":
        score += 20
    if book.storage_key:
        score += 10
    if book.category == "Imported":
        score += 5
    if book.category == "New-folder":
        score -= 3
    if book.category.startswith("Book Reports") or "book reports" in book.category.lower():
        score -= 40
    if key.endswith("/report.pdf") or key.endswith("\\report.pdf"):
        score -= 50
    if _title_key(book.title) == "report":
        score -= 60
    score += min(len(book.title), 120) // 40
    return score


def _pick_winner(group: list[LibraryBook]) -> LibraryBook:
    return max(group, key=lambda book: (_score(book), book.created_at))


async def _merge_reading(
    session,
    winner_id: UUID,
    loser_id: UUID,
) -> None:
    rows = (
        await session.execute(
            select(LibraryReadingStatus).where(LibraryReadingStatus.book_id == loser_id)
        )
    ).scalars().all()
    for row in rows:
        existing = await session.get(
            LibraryReadingStatus,
            {"user_id": row.user_id, "book_id": winner_id},
        )
        if existing is None:
            row.book_id = winner_id
            continue
        if (row.last_page or 0) > (existing.last_page or 0):
            existing.last_page = row.last_page
        if row.status and not existing.status:
            existing.status = row.status
        await session.delete(row)


async def _merge_bookmarks(session, winner_id: UUID, loser_id: UUID) -> None:
    rows = (
        await session.execute(select(LibraryBookmark).where(LibraryBookmark.book_id == loser_id))
    ).scalars().all()
    for row in rows:
        existing = await session.get(
            LibraryBookmark,
            {"user_id": row.user_id, "book_id": winner_id},
        )
        if existing is None:
            row.book_id = winner_id
        else:
            await session.delete(row)


async def run(dry_run: bool) -> None:
    async with AsyncSessionLocal() as session:
        books = (
            await session.execute(select(LibraryBook).where(LibraryBook.status == "published"))
        ).scalars().all()
        groups: dict[str, list[LibraryBook]] = defaultdict(list)
        for book in books:
            groups[_title_key(book.title)].append(book)

        dup_groups = {key: items for key, items in groups.items() if len(items) > 1}
        to_delete: list[LibraryBook] = []

        for key, items in dup_groups.items():
            if key == "report":
                to_delete.extend(items)
                continue
            winner = _pick_winner(items)
            for book in items:
                if book.id != winner.id:
                    to_delete.append(book)

        lone_reports = [b for b in books if _title_key(b.title) == "report" and b not in to_delete]
        to_delete.extend(lone_reports)
        for book in books:
            if _title_key(book.title) in _REMOVED_TITLES and book not in to_delete:
                to_delete.append(book)

        print(f"Published rows: {len(books)}")
        print(f"Unique titles: {len(groups)}")
        print(f"Duplicate groups: {len(dup_groups)}")
        print(f"Rows to remove: {len(to_delete)}")

        if dry_run:
            for book in to_delete[:15]:
                print(f"  DROP {book.id} | {book.category} | {book.title[:70]}")
            if len(to_delete) > 15:
                print(f"  ... and {len(to_delete) - 15} more")
            return

        keepers = {
            key: _pick_winner(items)
            for key, items in groups.items()
            if key != "report" and len(items) > 0
        }

        for book in to_delete:
            key = _title_key(book.title)
            if key == "report" or key in _REMOVED_TITLES:
                await session.execute(
                    delete(LibraryReadingStatus).where(LibraryReadingStatus.book_id == book.id)
                )
                await session.execute(delete(LibraryBookmark).where(LibraryBookmark.book_id == book.id))
                await session.execute(delete(LibraryBook).where(LibraryBook.id == book.id))
                continue
            winner = keepers[key]
            if book.id == winner.id:
                continue
            await _merge_bookmarks(session, winner.id, book.id)
            await _merge_reading(session, winner.id, book.id)
            await session.execute(delete(LibraryBook).where(LibraryBook.id == book.id))

        await session.commit()
        remaining = (
            await session.execute(
                select(LibraryBook).where(LibraryBook.status == "published")
            )
        ).scalars().all()
        print(f"Remaining published: {len(remaining)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    asyncio.run(run(args.dry_run))


if __name__ == "__main__":
    main()
