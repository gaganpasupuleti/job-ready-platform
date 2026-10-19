"""Push books to Cloudflare R2 under library/import/ and register them in the catalog (no admin UI).

Local folder (PDF or EPUB — EPUB is converted with Calibre):
  python scripts/library_r2_ingest.py push "C:\\path\\to\\books"

Manual R2 upload (PDF only under library/import/…):
  python scripts/library_r2_ingest.py sync
"""

from __future__ import annotations

import argparse
import asyncio
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.library.epub_convert import epub_to_pdf_file
from app.library.import_keys import IMPORT_PREFIX
from app.library.storage import StorageError, library_storage
from app.models.enums import UserRole
from app.models.user import User
from app.services.library_service import LibraryService

_SLUG = re.compile(r"[^a-zA-Z0-9._-]+")


def _segment(text: str) -> str:
    cleaned = _SLUG.sub("-", text.strip()).strip("-")
    return cleaned[:80] or "Imported"


def _import_key(category: str, filename: str) -> str:
    name = Path(filename).name
    if not name.lower().endswith(".pdf"):
        name = f"{Path(name).stem}.pdf"
    return f"{IMPORT_PREFIX}{_segment(category)}/{name}"


def push_folder(folder: Path) -> list[str]:
    store = library_storage()
    uploaded: list[str] = []
    def _include(path: Path) -> bool:
        parts = {part.lower() for part in path.parts}
        if "role_reports" in parts or "book reports" in " ".join(parts):
            return False
        name = path.name.lower()
        if name == "report.pdf":
            return False
        if "codequest" in name and "license" in name:
            return False
        return True

    pdfs = sorted(p for p in folder.rglob("*.pdf") if p.is_file() and _include(p))
    epubs = sorted(p for p in folder.rglob("*.epub") if p.is_file() and _include(p))
    if not pdfs and not epubs:
        raise SystemExit("No .pdf or .epub files in this folder.")

    work: list[tuple[Path, Path, bool]] = [(p, p, False) for p in pdfs]
    for epub_path in epubs:
        print(f"CONVERT {epub_path.name} (EPUB → PDF)…", file=sys.stderr)
        temp_pdf = epub_to_pdf_file(epub_path)
        work.append((epub_path, temp_pdf, True))

    for source, pdf_path, delete_temp in work:
        rel = source.parent.relative_to(folder)
        category = rel.as_posix() if rel.parts else "Imported"
        pdf_name = f"{source.stem}.pdf"
        key = _import_key(category, pdf_name)
        body = pdf_path.read_bytes()
        if not body.startswith(b"%PDF"):
            print(f"Skip (not PDF): {source}", file=sys.stderr)
            if delete_temp:
                pdf_path.unlink(missing_ok=True)
            continue
        store.put(key, body)
        if not store.exists(key):
            if delete_temp:
                pdf_path.unlink(missing_ok=True)
            raise SystemExit(f"Upload could not be verified: {key}")
        uploaded.append(key)
        print(f"UPLOAD  {key}")
        if delete_temp:
            pdf_path.unlink(missing_ok=True)
    return uploaded


async def sync_catalog() -> None:
    async with AsyncSessionLocal() as session:
        admin = (
            await session.execute(select(User).where(User.role == UserRole.ADMIN).limit(1))
        ).scalar_one_or_none()
        if admin is None:
            raise SystemExit("No admin user in the database.")
        svc = LibraryService(session)
        books = await svc.sync_import_catalog(admin)
        if not books:
            print("SYNC  no new PDFs under library/import/")
            return
        for book in books:
            print(f"SYNC  {book.title} [{book.category}] -> {book.id}")


def main() -> None:
    parser = argparse.ArgumentParser(description="R2 library import drop zone")
    sub = parser.add_subparsers(dest="command", required=True)
    push = sub.add_parser("push", help="Upload PDFs/EPUBs from a folder to library/import/ on R2")
    push.add_argument("folder", type=Path)
    sub.add_parser("sync", help="Create catalog rows for PDFs already in library/import/")
    args = parser.parse_args()
    try:
        if args.command == "push":
            push_folder(args.folder.resolve())
            asyncio.run(sync_catalog())
        else:
            asyncio.run(sync_catalog())
    except StorageError as exc:
        raise SystemExit(exc.message) from exc
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    main()
