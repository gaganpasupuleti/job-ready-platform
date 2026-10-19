"""Bulk-import library PDFs from a folder (admin API). EPUB is skipped — convert to PDF first."""

from __future__ import annotations

import argparse
import json
import mimetypes
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

MAX_TITLE = 200
MAX_CATEGORY = 80


def _request(url: str, method: str, token: str | None = None, data: bytes | None = None, headers: dict[str, str] | None = None) -> dict | list:
    hdrs = dict(headers or {})
    if token:
        hdrs["Authorization"] = f"Bearer {token}"
    if data is not None and "Content-Type" not in hdrs:
        hdrs["Content-Type"] = "application/json"
    req = Request(url, data=data, headers=hdrs, method=method)
    try:
        with urlopen(req, timeout=120) as resp:
            body = resp.read()
            return json.loads(body) if body else {}
    except HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        raise SystemExit(f"{method} {url} failed ({exc.code}): {detail}") from exc
    except URLError as exc:
        raise SystemExit(f"Could not reach {url}: {exc}") from exc


def _post_json(base: str, path: str, token: str | None, payload: dict) -> dict:
    url = f"{base.rstrip('/')}{path}"
    return _request(url, "POST", token, json.dumps(payload).encode())


def login(base: str, email: str, password: str) -> str:
    out = _post_json(base, "/api/v1/auth/login", None, {"email": email, "password": password})
    token = out.get("access_token")
    if not token:
        raise SystemExit("Login did not return an access token.")
    return token


def patch_book(base: str, token: str, book_id: str, body: dict) -> dict:
    url = f"{base.rstrip('/')}/api/v1/admin/library/books/{book_id}"
    return _request(url, "PATCH", token, json.dumps(body).encode())


def upload_pdf(base: str, token: str, book_id: str, pdf: Path) -> dict:
    url = f"{base.rstrip('/')}/api/v1/admin/library/books/{book_id}/file"
    content = pdf.read_bytes()
    if not content.startswith(b"%PDF"):
        raise ValueError(f"Not a PDF: {pdf}")
    mime = mimetypes.guess_type(pdf.name)[0] or "application/pdf"
    boundary = "----jobready-library-import"
    body = b"".join(
        [
            f"--{boundary}\r\n".encode(),
            f'Content-Disposition: form-data; name="file"; filename="{pdf.name}"\r\n'.encode(),
            f"Content-Type: {mime}\r\n\r\n".encode(),
            content,
            f"\r\n--{boundary}--\r\n".encode(),
        ]
    )
    req = Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    with urlopen(req, timeout=300) as resp:
        return json.loads(resp.read())


def title_from_path(pdf: Path, root: Path) -> str:
    text = pdf.stem.replace("_", " ").strip()
    if len(text) > MAX_TITLE:
        text = text[: MAX_TITLE - 1].rstrip() + "…"
    return text or "Untitled"


def category_from_path(pdf: Path, root: Path, default: str) -> str:
    parent = pdf.parent
    if parent != root and parent.name.strip():
        name = parent.name.strip()
        return name[:MAX_CATEGORY]
    return default[:MAX_CATEGORY]


def main() -> None:
    parser = argparse.ArgumentParser(description="Import PDFs from a folder into JobReady library.")
    parser.add_argument("folder", type=Path, help="Folder to scan (recursive) for .pdf files")
    parser.add_argument("--api", default="http://127.0.0.1:8020", help="API base URL")
    parser.add_argument("--email", default="admin@jobready.dev")
    parser.add_argument("--password", default="Admin123!")
    parser.add_argument("--author", default="Bulk import")
    parser.add_argument("--category", default="Imported", help="Default category when PDF is in folder root")
    parser.add_argument("--publish", action="store_true", help="Set status to published after upload")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    root = args.folder.resolve()
    if not root.is_dir():
        raise SystemExit(f"Not a folder: {root}")

    pdfs = sorted(root.rglob("*.pdf"))
    epubs = sorted(root.rglob("*.epub"))
    if epubs:
        print(f"Skipping {len(epubs)} EPUB file(s) — library only accepts PDF. Convert first.", file=sys.stderr)
        for path in epubs[:5]:
            print(f"  - {path}", file=sys.stderr)
        if len(epubs) > 5:
            print(f"  … and {len(epubs) - 5} more", file=sys.stderr)
    if not pdfs:
        raise SystemExit("No .pdf files found under this folder.")

    if args.dry_run:
        for pdf in pdfs:
            print(f"[dry-run] {title_from_path(pdf, root)} | {category_from_path(pdf, root, args.category)} | {pdf}")
        return

    token = login(args.api, args.email, args.password)
    for pdf in pdfs:
        title = title_from_path(pdf, root)
        category = category_from_path(pdf, root, args.category)
        created = _post_json(
            args.api,
            "/api/v1/admin/library/books",
            token,
            {
                "title": title,
                "author": args.author,
                "description": f"Imported from {pdf.name}.",
                "category": category,
                "status": "draft",
            },
        )
        book_id = created["id"]
        upload_pdf(args.api, token, book_id, pdf)
        if args.publish:
            patch_book(args.api, token, book_id, {"status": "published"})
        print(f"OK  {title} ({book_id})")


if __name__ == "__main__":
    main()
