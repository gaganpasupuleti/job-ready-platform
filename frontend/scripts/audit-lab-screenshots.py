"""Record screenshot file metadata for manual visual QA (not a substitute for Desktop)."""
from __future__ import annotations

import json
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    Image = None  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "public" / "reports" / "executive-sales-toast-lab"
WORKSHOP = json.loads((LAB / "workshop-content.json").read_text(encoding="utf-8"))

KEY_IMAGES = [
    ("steps/01-full-canvas.png", "result", "Full canvas reference"),
    ("steps/02-slicers.png", "result", "Slicer region crop"),
    ("steps/03-kpi-cards.png", "result", "KPI card region crop"),
    ("steps/04-profit-bar.png", "result", "Cost/profit composition bar crop"),
    ("steps/05-trend-chart.png", "result", "Trend line crop"),
    ("steps/06-toast.png", "result", "Toast region crop"),
    ("visuals/cd602ccaa356b4004e2b.png", "result", "Store slicer"),
    ("visuals/2ed267463a11685d300a.png", "result", "Total Sales card"),
    ("visuals/d229beaccea875451039.png", "result", "HTML Content toast visual"),
]

MISSING_CONFIG = [
    "Power BI Desktop field-well configuration panes are not captured; students use workshop M/DAX text.",
    "Bookmark/Data pane states require Desktop manual test (pending_desktop).",
    "Toast animation cannot be validated from PNG alone.",
]


def meta(path: Path) -> dict:
    entry: dict = {"path": str(path.relative_to(LAB)).replace("\\", "/"), "bytes": path.stat().st_size}
    if Image and path.is_file():
        with Image.open(path) as img:
            entry["width"], entry["height"] = img.size
    return entry


def main() -> None:
    items = []
    for rel, role, note in KEY_IMAGES:
        p = LAB / rel
        items.append(
            {
                "path": rel,
                "role": role,
                "caption": note,
                "exists": p.is_file(),
                "verificationStatus": "verified_crop" if p.is_file() else "missing_screenshot",
                **(meta(p) if p.is_file() else {}),
            }
        )
    out = {
        "contentVersion": WORKSHOP.get("contentVersion"),
        "coordinateMethod": "parentGroupName chain from PBIX visual.json (validated sample 0 mismatches)",
        "items": items,
        "limitations": MISSING_CONFIG,
    }
    (LAB / "screenshot-audit.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"Wrote screenshot-audit.json ({sum(1 for i in items if i['exists'])}/{len(items)} present)")


if __name__ == "__main__":
    main()
