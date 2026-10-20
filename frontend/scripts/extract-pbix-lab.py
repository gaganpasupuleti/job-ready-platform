"""Extract datasets, DAX, Power Query, relationships, and visual snips from a .pbix.

Does not modify workshop-content.json — run regenerate-power-bi-lab.ps1 for the full pipeline.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any

from pbixray import PBIXRay

EXTRACTOR_VERSION = "2.1.0"
CONTENT_VERSION = "1.0.0"

PAGE_WIDTH = 1280.0
PAGE_HEIGHT = 780.0

# Report canvas inside a Power BI Desktop window screenshot (not 0,0 — ribbon + panes sit outside).
DEFAULT_CANVAS_RECT = {"left": 8, "top": 198, "width": 1270, "height": 785}

SKIP_VISUAL_TYPES = frozenset({"shape", "image", "actionButton", "unknown"})

VISUAL_HOW_TO: dict[str, str] = {
    "card": "Insert → Card. Drag the measure into the **Fields** well. Format font/size in Visual formatting.",
    "lineChart": "Insert → Line chart. Axis: date column. Values: measure. Add markers / analytics as needed.",
    "clusteredColumnChart": "Insert → Clustered column chart. Axis: category. Values: measure(s).",
    "hundredPercentStackedBarChart": "Insert → 100% stacked bar chart. Use for cost vs profit composition.",
    "slicer": "Insert → Slicer. Drag the filter column. Set single-select or dropdown in slicer settings.",
    "textbox": "Insert → Text box. Type title text or bind a measure for dynamic titles.",
    "image": "Insert → Image. Use button assets from the report theme or your own PNGs.",
    "shape": "Insert → Shape for layout chrome (lines, rectangles).",
    "htmlContent443BE3AD55E043BF878BED274D3A6855": "Get the HTML Content custom visual. Bind Toast HTML + CSS measures.",
}


def _collect_fields(node: Any, found: set[str]) -> None:
    if isinstance(node, dict):
        if "nativeQueryRef" in node and isinstance(node["nativeQueryRef"], str):
            found.add(node["nativeQueryRef"])
        if "queryRef" in node and isinstance(node["queryRef"], str):
            found.add(node["queryRef"])
        for value in node.values():
            _collect_fields(value, found)
    elif isinstance(node, list):
        for item in node:
            _collect_fields(item, found)


def _absolute_position(raw: dict[str, Any], by_name: dict[str, dict[str, Any]]) -> tuple[float, float]:
    pos = raw.get("position") or {}
    x, y = float(pos.get("x", 0)), float(pos.get("y", 0))
    parent = raw.get("parentGroupName")
    if parent and parent in by_name:
        px, py = _absolute_position(by_name[parent], by_name)
        return x + px, y + py
    return x, y


def _visual_title(vtype: str, fields: set[str]) -> str:
    title = next(iter(sorted(fields)), vtype)
    for ref in fields:
        if "Measures." in ref or "[" in ref:
            title = ref.split(".")[-1] if "." in ref else ref
            break
    return title


def _parse_visuals_from_page_prefix(
    zf: zipfile.ZipFile, prefix: str, page_w: float, page_h: float
) -> list[dict[str, Any]]:
    by_name: dict[str, dict[str, Any]] = {}
    for name in zf.namelist():
        if not name.startswith(f"{prefix}/visuals/") or not name.endswith("/visual.json"):
            continue
        raw = json.loads(zf.read(name))
        by_name[str(raw.get("name", ""))] = raw

    visuals: list[dict[str, Any]] = []
    for raw in by_name.values():
        pos = raw.get("position") or {}
        w = float(pos.get("width", 0))
        h = float(pos.get("height", 0))
        if w < 72 or h < 32:
            continue
        visual = raw.get("visual") or {}
        vtype = str(visual.get("visualType") or "unknown")
        fields: set[str] = set()
        _collect_fields(visual.get("query"), fields)
        if vtype in ("unknown", "group") and not fields:
            continue
        ax, ay = _absolute_position(raw, by_name)
        visuals.append(
            {
                "id": raw.get("name", ""),
                "visualType": vtype,
                "title": _visual_title(vtype, fields),
                "fields": sorted(fields),
                "x": ax,
                "y": ay,
                "width": w,
                "height": h,
                "howTo": VISUAL_HOW_TO.get(
                    vtype, "Recreate this visual type in Power BI and bind the same fields."
                ),
                "snip": f"visuals/{raw.get('name', 'unknown')}.png",
            }
        )
    return visuals


def _parse_visuals_from_layout(zf: zipfile.ZipFile) -> tuple[list[dict[str, Any]], float, float]:
    """Legacy PBIX stores a single compressed Report/Layout blob instead of per-page JSON."""
    if "Report/Layout" not in zf.namelist():
        return [], PAGE_WIDTH, PAGE_HEIGHT
    try:
        import zlib

        raw = zf.read("Report/Layout")
        if raw[:2] == b"\x1f\x8b":
            raw = zlib.decompress(raw, zlib.MAX_WBITS | 16)
        text = raw.decode("utf-16-le", errors="ignore")
        layout = json.loads(text)
    except (json.JSONDecodeError, OSError, UnicodeError):
        return [], PAGE_WIDTH, PAGE_HEIGHT

    page_w = float(layout.get("width", PAGE_WIDTH))
    page_h = float(layout.get("height", PAGE_HEIGHT))
    by_name: dict[str, dict[str, Any]] = {}
    for section in layout.get("sections", []):
        for visual_container in section.get("visualContainers", []):
            config_raw = visual_container.get("config")
            if not config_raw:
                continue
            try:
                config = json.loads(config_raw) if isinstance(config_raw, str) else config_raw
            except json.JSONDecodeError:
                continue
            name = str(config.get("name") or visual_container.get("id", ""))
            by_name[name] = {
                "name": name,
                "position": {
                    "x": visual_container.get("x", 0),
                    "y": visual_container.get("y", 0),
                    "width": visual_container.get("width", 0),
                    "height": visual_container.get("height", 0),
                },
                "visual": config.get("singleVisual") or {},
                "parentGroupName": config.get("parentGroupName"),
            }

    visuals: list[dict[str, Any]] = []
    for raw in by_name.values():
        pos = raw.get("position") or {}
        w = float(pos.get("width", 0))
        h = float(pos.get("height", 0))
        if w < 72 or h < 32:
            continue
        visual = raw.get("visual") or {}
        vtype = str(visual.get("visualType") or "unknown")
        fields: set[str] = set()
        _collect_fields(visual.get("query"), fields)
        if vtype in ("unknown", "group") and not fields:
            continue
        ax, ay = _absolute_position(raw, by_name)
        visuals.append(
            {
                "id": raw.get("name", ""),
                "visualType": vtype,
                "title": _visual_title(vtype, fields),
                "fields": sorted(fields),
                "x": ax,
                "y": ay,
                "width": w,
                "height": h,
                "howTo": VISUAL_HOW_TO.get(
                    vtype, "Recreate this visual type in Power BI and bind the same fields."
                ),
                "snip": f"visuals/{raw.get('name', 'unknown')}.png",
            }
        )
    return visuals, page_w, page_h


def _parse_visuals_from_pbix(pbix: Path) -> tuple[list[dict[str, Any]], float, float]:
    visuals: list[dict[str, Any]] = []
    page_w, page_h = PAGE_WIDTH, PAGE_HEIGHT
    with zipfile.ZipFile(pbix, "r") as zf:
        page_paths = [n for n in zf.namelist() if n.endswith("/page.json") and "/pages/" in n]
        for page_path in page_paths:
            page = json.loads(zf.read(page_path))
            page_w = float(page.get("width", PAGE_WIDTH))
            page_h = float(page.get("height", PAGE_HEIGHT))
            prefix = page_path.rsplit("/page.json", 1)[0]
            visuals.extend(_parse_visuals_from_page_prefix(zf, prefix, page_w, page_h))
        if not visuals:
            visuals, page_w, page_h = _parse_visuals_from_layout(zf)
    visuals.sort(key=lambda v: (v["y"], v["x"]))
    return visuals, page_w, page_h


def _export_relationships(model: PBIXRay) -> list[dict[str, Any]]:
    rel = model.relationships
    rows: list[dict[str, Any]] = []
    for _, row in rel.iterrows():
        rows.append(
            {
                "fromTable": str(row["FromTableName"]),
                "fromColumn": str(row["FromColumnName"]),
                "toTable": str(row["ToTableName"]),
                "toColumn": str(row["ToColumnName"]),
                "cardinality": str(row.get("Cardinality", "")),
                "crossFilter": str(row.get("CrossFilteringBehavior", "")),
                "active": bool(row.get("IsActive", True)),
            }
        )
    return rows


def _mermaid_er(relationships: list[dict[str, Any]]) -> str:
    lines = ["```mermaid", "erDiagram"]
    for r in relationships:
        # Dimension (one) on the left, fact Sales (many) on the right.
        dim_table, dim_col = r["toTable"], r["toColumn"]
        fact_table, fact_col = r["fromTable"], r["fromColumn"]
        safe = lambda s: re.sub(r"[^A-Za-z0-9_]", "_", s)
        lines.append(f'    {safe(dim_table)} ||--o{{ {safe(fact_table)} : "{dim_col} -> {fact_col}"')
    lines.append("```")
    return "\n".join(lines)


def _visual_to_pixels(
    v: dict[str, Any], canvas: dict[str, float], page_w: float, page_h: float
) -> tuple[int, int, int, int]:
    sx = canvas["width"] / page_w
    sy = canvas["height"] / page_h
    pad = 4
    left = int(canvas["left"] + v["x"] * sx) - pad
    top = int(canvas["top"] + v["y"] * sy) - pad
    right = int(canvas["left"] + (v["x"] + v["width"]) * sx) + pad
    bottom = int(canvas["top"] + (v["y"] + v["height"]) * sy) + pad
    return left, top, right, bottom


def _save_canvas_reference(preview: Path, canvas: dict[str, float], out_path: Path) -> None:
    try:
        from PIL import Image
    except ImportError:
        return
    if not preview.is_file():
        return
    img = Image.open(preview)
    crop = img.crop(
        (
            int(canvas["left"]),
            int(canvas["top"]),
            int(canvas["left"] + canvas["width"]),
            int(canvas["top"] + canvas["height"]),
        )
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    crop.save(out_path, "PNG")


def _crop_union(
    img: Any, visuals: list[dict[str, Any]], canvas: dict[str, float], page_w: float, page_h: float, out_path: Path
) -> None:
    if not visuals:
        return
    left = top = 10_000
    right = bottom = 0
    for v in visuals:
        l, t, r, b = _visual_to_pixels(v, canvas, page_w, page_h)
        left = min(left, l)
        top = min(top, t)
        right = max(right, r)
        bottom = max(bottom, b)
    left = max(0, left)
    top = max(0, top)
    right = min(img.width, right)
    bottom = min(img.height, bottom)
    if right - left < 48 or bottom - top < 32:
        return
    img.crop((left, top, right, bottom)).save(out_path, "PNG")


def _build_steps(
    visuals: list[dict[str, Any]],
    preview: Path,
    canvas: dict[str, float],
    page_w: float,
    page_h: float,
    out_dir: Path,
) -> list[dict[str, Any]]:
    try:
        from PIL import Image
    except ImportError:
        return []

    if not preview.is_file():
        return []

    img = Image.open(preview)
    steps_dir = out_dir / "steps"
    steps_dir.mkdir(parents=True, exist_ok=True)

    def pick(fn: Any) -> list[dict[str, Any]]:
        return [v for v in visuals if v["visualType"] not in SKIP_VISUAL_TYPES and fn(v)]

    slicers = pick(
        lambda v: v["visualType"] == "slicer"
        and "Percentile" not in v["title"]
        and (
            "storelocations" in " ".join(v["fields"]).lower()
            or "Salesteam" in " ".join(v["fields"])
            or "Products" in " ".join(v["fields"])
        )
    )

    kpi_cards = pick(
        lambda v: v["visualType"] == "card"
        and v["y"] < 200
        and "diff" not in v["title"].lower()
        and "Formatted" not in v["title"]
    )
    line_charts = pick(lambda v: v["visualType"] in ("lineChart", "lineClusteredColumnComboChart"))
    line_charts.sort(key=lambda v: v["width"] * v["height"], reverse=True)
    toast = pick(lambda v: "htmlContent" in v["visualType"] or "Toast" in v["title"])

    step_defs: list[tuple[str, str, str, list[dict[str, Any]]]] = [
        (
            "01-full-canvas",
            "See the finished page",
            "Use this as your target layout (1280×780). Match spacing before fine-tuning formats.",
            visuals,
        ),
        (
            "02-slicers",
            "Step 1 — Slicers",
            "Insert → Slicer. Add **Stores** (storelocations.name), **Sales Team** (Salesteams), **Products** (Products_Data). Place top-right; set dropdown style.",
            slicers,
        ),
        (
            "03-kpi-cards",
            "Step 2 — KPI cards",
            "Insert → Card for each measure: Total Sales, Profit Margin %, Total Orders, % of Target (monthly), Average Daily Sales. Use the DAX block list for formulas.",
            kpi_cards,
        ),
        (
            "04-profit-bar",
            "Step 3 — Profit composition",
            "Insert → 100% stacked bar. Values: Total Cost & Total Profit measures (see DAX). Place under Profit Margin card.",
            pick(lambda v: v["visualType"] == "hundredPercentStackedBarChart"),
        ),
        (
            "05-trend-chart",
            "Step 4 — Sales trend",
            "Insert → Line chart. Axis: Date Table[Date]. Values: Total Sales. Add month buttons + D/W/M bookmarks (optional).",
            line_charts[:1],
        ),
        (
            "06-toast",
            "Step 5 — Toast notification",
            "Add HTML Content custom visual. Bind **Toast Notification** and **Toast CSS** measures from the DAX list.",
            toast,
        ),
    ]

    steps: list[dict[str, Any]] = []
    for idx, (file_id, title, body, group) in enumerate(step_defs, start=1):
        snip = f"steps/{file_id}.png"
        if file_id == "01-full-canvas":
            _save_canvas_reference(preview, canvas, out_dir / snip)
        else:
            _crop_union(img, group, canvas, page_w, page_h, out_dir / snip)
        steps.append(
            {
                "step": idx,
                "id": file_id,
                "title": title,
                "instructions": body,
                "snip": snip,
                "visualCount": len(group),
            }
        )
    return steps


def _crop_snips(
    preview: Path,
    visuals: list[dict[str, Any]],
    out_vis: Path,
    page_w: float,
    page_h: float,
    canvas: dict[str, float],
) -> None:
    if not preview.is_file():
        return
    try:
        from PIL import Image
    except ImportError:
        return
    out_vis.mkdir(parents=True, exist_ok=True)
    img = Image.open(preview)
    for v in visuals:
        if v["visualType"] in SKIP_VISUAL_TYPES:
            continue
        left, top, right, bottom = _visual_to_pixels(v, canvas, page_w, page_h)
        left = max(0, left)
        top = max(0, top)
        right = min(img.width, right)
        bottom = min(img.height, bottom)
        if right - left < 40 or bottom - top < 24:
            continue
        crop = img.crop((left, top, right, bottom))
        crop.save(out_vis / f"{v['id']}.png", "PNG")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pbix", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--preview", type=Path, default=None, help="Full-page PNG for visual crops")
    parser.add_argument(
        "--canvas-rect",
        type=str,
        default=None,
        help='JSON object {"left":8,"top":198,"width":1270,"height":785}',
    )
    args = parser.parse_args()

    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    data_dir = out / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    model = PBIXRay(str(args.pbix))

    tables_meta: list[dict[str, object]] = []
    for table in model.tables:
        df = model.get_table(table)
        safe = table.replace(" ", "_")
        csv_path = data_dir / f"{safe}.csv"
        df.to_csv(csv_path, index=False)
        tables_meta.append({"name": table, "file": f"data/{safe}.csv", "rows": len(df)})

    measures = model.dax_measures
    measures.to_csv(out / "dax-measures.csv", index=False)
    measure_blocks: list[dict[str, str]] = []
    for _, row in measures.iterrows():
        measure_blocks.append(
            {
                "table": str(row.get("TableName", "")),
                "name": str(row.get("MeasureName", row.get("Name", row.get("Measure", "")))),
                "expression": str(row.get("Expression", row.get("DAX", ""))),
            }
        )

    pq = model.power_query
    pq.to_csv(out / "power-query.csv", index=False)
    pq_blocks: list[dict[str, str]] = []
    for _, row in pq.iterrows():
        pq_blocks.append(
            {
                "table": str(row.get("TableName", row.get("Table", row.get("Name", "")))),
                "expression": str(row.get("Expression", row.get("M", ""))),
            }
        )

    relationships = _export_relationships(model)
    visuals, page_w, page_h = _parse_visuals_from_pbix(args.pbix)
    if not visuals:
        print("No visuals parsed — unsupported layout or empty report.", file=sys.stderr)
        sys.exit(2)

    preview = args.preview
    if preview is None:
        preview = args.pbix.parent / "executive-sales-toast.png"
    canvas = dict(DEFAULT_CANVAS_RECT)
    if args.canvas_rect:
        canvas.update(json.loads(args.canvas_rect))
    _save_canvas_reference(preview, canvas, out / "canvas-reference.png")
    build_steps = _build_steps(visuals, preview, canvas, page_w, page_h, out)
    (out / "build-steps.json").write_text(json.dumps(build_steps, indent=2), encoding="utf-8")
    _crop_snips(preview, visuals, out / "visuals", page_w, page_h, canvas)

    rel_md = "# Model relationships\n\n"
    rel_md += "Create these in **Model view** → **Manage relationships** (or drag columns between tables).\n\n"
    rel_md += "| From | Column | To | Column | Cardinality | Cross-filter |\n"
    rel_md += "|------|--------|-----|--------|-------------|-------------|\n"
    for r in relationships:
        rel_md += (
            f"| {r['fromTable']} | {r['fromColumn']} | {r['toTable']} | {r['toColumn']} | "
            f"{r['cardinality']} | {r['crossFilter']} |\n"
        )
    rel_md += "\n" + _mermaid_er(relationships) + "\n"

    (out / "relationships.json").write_text(json.dumps(relationships, indent=2), encoding="utf-8")
    (out / "relationships.md").write_text(rel_md, encoding="utf-8")
    (out / "visuals.json").write_text(json.dumps(visuals, indent=2), encoding="utf-8")

    pbix_hash = _sha256_file(args.pbix)
    preview_prov = (
        {
            "path": str(preview),
            "sha256": _sha256_file(preview) if preview.is_file() else None,
        }
        if preview
        else None
    )
    manifest = {
        "tables": tables_meta,
        "measureCount": len(measure_blocks),
        "queryCount": len(pq_blocks),
        "relationshipCount": len(relationships),
        "visualCount": len(visuals),
        "buildStepCount": len(build_steps),
        "pageWidth": page_w,
        "pageHeight": page_h,
        "canvasRect": canvas,
        "previewImage": "../executive-sales-toast.png",
        "canvasReference": "canvas-reference.png",
        "contentVersion": CONTENT_VERSION,
        "extractorVersion": EXTRACTOR_VERSION,
        "sourcePbixSha256": pbix_hash,
        "screenshotProvenance": {
            "preview": preview_prov,
            "canvasRect": canvas,
            "note": "Crops map report canvas coordinates through canvasRect; revalidate after Desktop theme or zoom changes.",
        },
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (out / "dax-measures.json").write_text(json.dumps(measure_blocks, indent=2), encoding="utf-8")
    (out / "power-query.json").write_text(json.dumps(pq_blocks, indent=2), encoding="utf-8")

    zip_path = out / "datasets.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for csv in data_dir.glob("*.csv"):
            zf.write(csv, arcname=f"data/{csv.name}")

    print(
        f"Wrote {out} ({len(tables_meta)} tables, {len(measure_blocks)} measures, "
        f"{len(relationships)} relationships, {len(visuals)} visuals)"
    )


if __name__ == "__main__":
    main()
