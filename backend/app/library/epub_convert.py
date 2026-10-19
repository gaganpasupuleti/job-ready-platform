"""Convert EPUB to PDF via Calibre ebook-convert (no extra Python deps)."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path


def calibre_ebook_convert() -> Path | None:
    found = shutil.which("ebook-convert")
    if found:
        return Path(found)
    for candidate in (
        Path(r"C:\Program Files\Calibre2\ebook-convert.exe"),
        Path(r"C:\Program Files (x86)\Calibre2\ebook-convert.exe"),
    ):
        if candidate.is_file():
            return candidate
    return None


def epub_to_pdf_file(epub: Path) -> Path:
    """Write a temporary PDF next to the system temp dir. Caller should delete it."""
    exe = calibre_ebook_convert()
    if exe is None:
        raise RuntimeError(
            "EPUB conversion requires Calibre (ebook-convert). "
            "Install from https://calibre-ebook.com/ or run: winget install calibre.calibre"
        )
    handle = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    handle.close()
    out = Path(handle.name)
    result = subprocess.run(
        [str(exe), str(epub), str(out)],
        capture_output=True,
        text=True,
        timeout=600,
    )
    if result.returncode != 0:
        out.unlink(missing_ok=True)
        detail = (result.stderr or result.stdout or "").strip()[-800:]
        raise RuntimeError(f"ebook-convert failed for {epub.name}: {detail}")
    if not out.read_bytes().startswith(b"%PDF"):
        out.unlink(missing_ok=True)
        raise RuntimeError(f"ebook-convert did not produce a valid PDF for {epub.name}")
    return out
