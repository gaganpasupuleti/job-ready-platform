"""R2 drop zone: library/import/… PDFs are registered into the catalog without the admin form."""

import re
from pathlib import PurePosixPath

IMPORT_PREFIX = "library/import/"

_OBJECT_KEY = re.compile(r"^library/books/[0-9a-fA-F-]{36}/[0-9a-f]{32}\.pdf$")
_IMPORT_KEY = re.compile(r"^library/import/(?:[^/]+/)*[^/]+\.pdf$", re.IGNORECASE)


def storage_key_allowed(key: str) -> bool:
    return bool(_OBJECT_KEY.fullmatch(key) or _IMPORT_KEY.fullmatch(key))


def metadata_from_import_key(key: str) -> tuple[str, str, str]:
    """Return title, category, description from library/import/{category}/file.pdf."""
    if not _IMPORT_KEY.fullmatch(key):
        raise ValueError(f"Not an import key: {key}")
    parts = PurePosixPath(key).parts
    # library / import / [category...] / file.pdf
    filename = parts[-1]
    title = filename[:-4].replace("_", " ").replace("-", " ").strip() or "Untitled"
    if len(parts) >= 4:
        category = parts[2] if len(parts) == 4 else "/".join(parts[2:-1])
    else:
        category = "Imported"
    category = category.replace("_", " ").strip()[:80] or "Imported"
    if len(title) > 200:
        title = title[:199].rstrip() + "…"
    description = f"Catalog entry for {filename} in Cloudflare storage."
    return title, category, description
