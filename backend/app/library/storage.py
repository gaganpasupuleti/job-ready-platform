"""Library object storage. Students never see keys or credentials."""

import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import UUID

from app.core.config import settings
from app.library.fixtures import LOCAL_FIXTURE_KEY, fixture_pdf_bytes
from app.library.r2 import R2Config, presign_get, signed_headers

_OBJECT_KEY = re.compile(r"^library/books/[0-9a-fA-F-]{36}/[0-9a-f]{32}\.pdf$")


class StorageError(Exception):
    def __init__(self, message: str, status_code: int = 503):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class LibraryStorage:
    def put(self, key: str, body: bytes) -> None:
        raise NotImplementedError

    def delete(self, key: str) -> None:
        raise NotImplementedError

    def exists(self, key: str) -> bool:
        raise NotImplementedError

    def presign_get(self, key: str, book_id: UUID) -> str:
        raise NotImplementedError

    def read_bytes(self, key: str) -> bytes | None:
        raise NotImplementedError


class UnconfiguredStorage(LibraryStorage):
    def put(self, key: str, body: bytes) -> None:
        raise StorageError("PDF storage is not configured.", 503)

    def delete(self, key: str) -> None:
        raise StorageError("PDF storage is not configured.", 503)

    def exists(self, key: str) -> bool:
        raise StorageError("PDF storage is not configured.", 503)

    def presign_get(self, key: str, book_id: UUID) -> str:
        raise StorageError("PDF storage is not configured.", 503)

    def read_bytes(self, key: str) -> bytes | None:
        raise StorageError("PDF storage is not configured.", 503)


class R2Storage(LibraryStorage):
    """Private bucket. Objects are not fetched through this API."""

    def __init__(self, config: R2Config):
        self.config = config

    def put(self, key: str, body: bytes) -> None:
        self._request("PUT", key, body)

    def delete(self, key: str) -> None:
        try:
            self._request("DELETE", key, None)
        except StorageError as exc:
            if exc.status_code == 404:
                return
            raise

    def exists(self, key: str) -> bool:
        try:
            self._request("HEAD", key, None)
            return True
        except StorageError as exc:
            if exc.status_code == 404:
                return False
            raise

    def presign_get(self, key: str, book_id: UUID) -> str:
        return presign_get(self.config, key, datetime.now(timezone.utc), expires=300)

    def read_bytes(self, key: str) -> bytes | None:
        return None

    def _request(self, method: str, key: str, body: bytes | None) -> None:
        url, headers = signed_headers(self.config, method, key, datetime.now(timezone.utc))
        if method == "PUT":
            headers["Content-Type"] = "application/pdf"
        request = Request(url, data=body, headers=headers, method=method)
        try:
            with urlopen(request, timeout=30) as response:
                response.read()
        except HTTPError as exc:
            if exc.code == 404:
                raise StorageError("This PDF file is missing.", 404) from None
            raise StorageError("PDF storage could not be reached.", 503) from None
        except URLError:
            raise StorageError("PDF storage could not be reached.", 503) from None


class DevDiskStorage(LibraryStorage):
    """Development files on disk. Production never uses this store."""

    def __init__(self, root: Path):
        self.root = root

    def put(self, key: str, body: bytes) -> None:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)

    def delete(self, key: str) -> None:
        if key == LOCAL_FIXTURE_KEY:
            return
        path = self._path(key)
        if path.exists():
            path.unlink()

    def exists(self, key: str) -> bool:
        if key == LOCAL_FIXTURE_KEY:
            return True
        return self._path(key).is_file()

    def presign_get(self, key: str, book_id: UUID) -> str:
        return f"/api/v1/library/books/{book_id}/file"

    def read_bytes(self, key: str) -> bytes | None:
        if key == LOCAL_FIXTURE_KEY:
            return fixture_pdf_bytes()
        path = self._path(key)
        if not path.is_file():
            return None
        return path.read_bytes()

    def _path(self, key: str) -> Path:
        if not _OBJECT_KEY.fullmatch(key):
            raise StorageError("This PDF file is missing.", 404)
        return self.root.joinpath(*key.split("/"))


def library_storage() -> LibraryStorage:
    if settings.library_storage_configured:
        return R2Storage(
            R2Config(
                account_id=settings.library_r2_account_id.strip(),
                bucket=settings.library_r2_bucket.strip(),
                access_key_id=settings.library_r2_access_key_id.strip(),
                secret_access_key=settings.library_r2_secret_access_key.strip(),
            )
        )
    if settings.app_env.lower() in {"production", "prod"}:
        return UnconfiguredStorage()
    root = settings.library_dev_object_dir.strip() or str(Path(__file__).resolve().parents[2] / "var" / "library-objects")
    return DevDiskStorage(Path(root))
