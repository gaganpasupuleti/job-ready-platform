"""Write manifest.json with content-file sha256 digests."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FILES = [
    "materials.json",
    "questions.json",
    "syllabus.json",
    "articles/crt-quant-percentages.md",
    "articles/crt-logical-patterns.md",
    "articles/crt-verbal-meaning.md",
    "articles/crt-di-tables.md",
    "articles/dsa-complexity.md",
    "articles/dsa-arrays-strings.md",
    "VIDEO_GAPS.md",
]


def main() -> None:
    items = []
    for rel in FILES:
        path = ROOT / rel
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        items.append({"path": rel.replace("\\", "/"), "sha256": digest})
    payload = {
        "batch_id": "2026-09-14-syllabus-001",
        "title": "CRT and DSA syllabus reading unit",
        "audience": ["Fresher", "Entry (1-2 yrs)"],
        "notes": [
            "Published lessons only. Coming-soon rows have no empty article pages.",
            "YouTube recommendations omitted; see VIDEO_GAPS.md.",
            "Mark-as-read remains reading progress only.",
        ],
        "items": items,
    }
    (ROOT / "manifest.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"batch_id": payload["batch_id"], "files": len(items)}, indent=2))


if __name__ == "__main__":
    main()
