"""Write manifest.json for the visual-learning article update.

This batch updates the six published CRT and DSA articles to version 2.
It does not replace the 2026-09-14 syllabus batch, and it does not change
lesson keys, syllabus keys, or question keys.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FILES = [
    "materials.json",
    "questions.json",
    "articles/crt-quant-percentages.md",
    "articles/crt-logical-patterns.md",
    "articles/crt-verbal-meaning.md",
    "articles/crt-di-tables.md",
    "articles/dsa-complexity.md",
    "articles/dsa-arrays-strings.md",
]


def main() -> None:
    items = []
    for rel in FILES:
        path = ROOT / rel
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        items.append({"path": rel.replace("\\", "/"), "sha256": digest})
    payload = {
        "batch_id": "2026-10-10-visual-learning-001",
        "title": "Visual diagrams for published CRT and DSA lessons",
        "audience": ["Fresher", "Entry (1-2 yrs)"],
        "notes": [
            "Version 2 article bodies for the six existing content keys. Syllabus rows and questions stay in the 2026-09-14 batch.",
            "Release order: merge the reviewed code, deploy the frontend so the six SVG files are served, verify those asset URLs, then run an explicitly approved import, then check a lesson as a signed-in student.",
            "Frontend deployment is required for the image renderer and the static files. A backend deployment is not required to render lesson Markdown.",
            "python scripts/content_batch.py accepts only --target local and refuses a remote database. Do not point it at production.",
        ],
        "items": items,
    }
    (ROOT / "manifest.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"batch_id": payload["batch_id"], "files": len(items)}, indent=2))


if __name__ == "__main__":
    main()
