"""Build workshop-content.json and student-facing docs from lab assets."""
from __future__ import annotations

import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "public" / "reports" / "executive-sales-toast-lab"
CONTENT_VERSION = "1.0.1"

EXCLUDED_MEASURES = [
    {
        "name": "H Percentile Scetter",
        "reason": "References missing disconnected table 'Higher Per (Store)'; not used on the main dashboard.",
    },
    {
        "name": "L Percentile Scetter",
        "reason": "References missing disconnected table 'Lower Per (store)'; not used on the main dashboard.",
    },
    {
        "name": "Color Formatting Scatter Chart",
        "reason": "Depends on excluded scatter percentile measures.",
    },
    {
        "name": "ranking_asc",
        "reason": "References missing field parameter table 'Number of Rows'.",
    },
    {
        "name": "ranking_desc",
        "reason": "References missing field parameter table 'Number of Rows'.",
    },
]

TOAST_CSS_FIXED = """
#toastBox {
  display: flex;
  align-items: center;
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  width: 100vw;
  padding: 16px 16px;
  background-color: #484848;
  border: 1px solid grey;
  border-radius: 8px 0px 0px 8px;
  box-shadow: 0px 4px 8px 0px rgba(0, 0, 0, 0.2);
  font-family: sans-serif;
  font-size: 16px;
  z-index: 9999;
  opacity: 0;
  animation: slideInOut 3.5s ease forwards;
}
""".strip()


def load_json(name: str):
    return json.loads((LAB / name).read_text(encoding="utf-8"))


def measure_catalog() -> list[dict]:
    measures = load_json("dax-measures.json")
    excluded = {m["name"] for m in EXCLUDED_MEASURES}
    return [m for m in measures if m["name"] not in excluded]


def topo_sort_measures(blocks: list[dict]) -> list[dict]:
    by_name = {b["name"]: b for b in blocks}
    deps: dict[str, set[str]] = {}
    for b in blocks:
        found = set(re.findall(r"\[([^\]]+)\]", b["expression"]))
        deps[b["name"]] = {d for d in found if d in by_name and d != b["name"]}
    ordered: list[dict] = []
    seen: set[str] = set()

    def visit(name: str) -> None:
        if name in seen:
            return
        seen.add(name)
        for d in sorted(deps.get(name, set())):
            visit(d)
        ordered.append(by_name[name])

    for name in sorted(by_name):
        visit(name)
    return ordered


def dax_block(table: str, name: str, expression: str) -> dict:
    expr = expression.strip()
    if not expr.startswith(name):
        expr = f"{name} =\n{expr}"
    return {"table": table, "name": name, "expression": expr}


def step(
    sid: str,
    stage_id: str,
    order: int,
    title: str,
    objective: str,
    actions: list[str],
    *,
    prerequisites: list[str] | None = None,
    expected: str = "",
    checklist: list[str] | None = None,
    mistakes: list[str] | None = None,
    images: list[dict] | None = None,
    dax: list[dict] | None = None,
    power_query: list[dict] | None = None,
    visual: dict | None = None,
    reference_notes: str = "",
    status: str = "verified",
) -> dict:
    return {
        "id": sid,
        "stageId": stage_id,
        "order": order,
        "title": title,
        "objective": objective,
        "prerequisites": prerequisites or [],
        "actions": actions,
        "dax": dax,
        "powerQuery": power_query,
        "visual": visual,
        "expectedResult": expected,
        "verificationChecklist": checklist or [],
        "commonMistakes": mistakes or [],
        "images": images or [],
        "referenceNotes": reference_notes,
        "verificationStatus": status,
    }


def build_steps() -> list[dict]:
    manifest = load_json("manifest.json")
    steps: list[dict] = []

    steps.append(
        step(
            "setup-01",
            "setup",
            1,
            "Know the target report",
            "Recognize the finished executive sales page you will rebuild from a blank PBIX.",
            [
                "Open the JobReady **Finished preview** (static PNG — interactions happen in Power BI Desktop).",
                "Note canvas size 1280×780 and the KPI + trend + toast layout.",
            ],
            images=[
                {
                    "src": "steps/01-full-canvas.png",
                    "caption": "Finished report canvas (reference).",
                    "alt": "Executive sales dashboard with KPI cards, slicers, trend chart, and toast area",
                    "role": "result",
                }
            ],
            expected="You can describe where slicers, KPIs, bars, trend, settings, and toast sit on the page.",
            checklist=["Preview image loads", "You understand this is a reference only"],
        )
    )
    steps.append(
        step(
            "setup-02",
            "setup",
            2,
            "Install tools",
            "Use a Power BI Desktop build that supports HTML Content custom visuals.",
            [
                "Install **Power BI Desktop** (tested with recent 2024–2025 builds).",
                "From AppSource in Desktop, add custom visual **HTML Content** (package id htmlContent443BE3AD55E043BF878BED274D3A6855, version 1.2.1.17 in the reference file).",
                "Create an empty folder for lab data, e.g. `C:\\JobReady\\executive-sales-data\\`.",
            ],
            prerequisites=["setup-01"],
            expected="Desktop opens, HTML Content visual is available in the visualizations pane.",
        )
    )
    steps.append(
        step(
            "setup-03",
            "setup",
            3,
            "Download the student kit",
            "Get CSVs and guides from JobReady.",
            [
                "Download **All datasets (.zip)** and extract into your data folder.",
                "Optional: download the reference `.pbix` only to compare — do not start from it for the graded rebuild.",
            ],
            prerequisites=["setup-02"],
            expected=f"Eight CSV files present ({manifest['tables'][0]['rows']}–{manifest['tables'][5]['rows']} rows).",
            checklist=["datasets.zip extracts without errors", "data folder path has no spaces issues in M"],
        )
    )
    steps.append(
        step(
            "setup-04",
            "setup",
            4,
            "Create a blank report",
            "Start from File → New to mirror the workshop path.",
            ["File → New → Blank report.", "Save as `Executive-Sales-Toast.pbix` in your lab folder."],
            prerequisites=["setup-03"],
            expected="Empty report with one blank page.",
        )
    )

    steps.append(
        step(
            "import-00",
            "import",
            0,
            "Create DataFolder parameter",
            "One path drives all CSV imports.",
            [
                "Home → Transform data → Manage Parameters → New.",
                "Name: **DataFolder**, type Text, current value = folder containing the eight CSV files (trailing backslash optional).",
            ],
            prerequisites=["setup-04"],
            expected="Parameter DataFolder appears under Parameters.",
            checklist=["Path opens without privacy errors on refresh"],
        )
    )

    import_queries = load_json("csv-import-queries.json")
    for order, q in enumerate(import_queries, start=1):
        table, file = q["table"], q["file"]
        steps.append(
            step(
                f"import-{order:02d}",
                "import",
                order,
                f"Import {table}",
                f"Load `{file}` as table **{table}** with explicit types.",
                [
                    "Home → Transform data → New Source → Blank Query.",
                    "Paste the M below (uses `DataFolder` parameter).",
                    f"Rename query to **{q.get('loadName', table)}** and ensure it loads to the model with table name **{table}**.",
                    "Close && Apply.",
                ],
                prerequisites=["import-00"] if order == 1 else [f"import-{order-1:02d}"],
                power_query=[
                    {
                        "name": table,
                        "parameter": "DataFolder",
                        "expression": q["expression"],
                    }
                ],
                reference_notes=(q.get("note") or "")
                + " Author Excel M is in power-query.json (reference only).",
                expected=f"Table **{table}** appears in the Fields pane.",
                checklist=[f"Table name is exactly `{table}`", "Refresh preview succeeds"],
            )
        )

    steps.append(
        step(
            "validate-01",
            "validate-data",
            1,
            "Row counts",
            "Confirm CSV loads match the packaged data.",
            ["Model view → select each table → verify row counts against the data dictionary."],
            prerequisites=["import-08"],
            expected="Sales 20,000 rows; Date Table 152; Products 47; stores 367; teams 28; percentile tables 10 each; Date M-W-D 3.",
            checklist=["Counts match manifest.json"],
        )
    )
    steps.append(
        step(
            "validate-02",
            "validate-data",
            2,
            "Sales keys",
            "Ensure foreign keys exist in dimensions.",
            [
                "In Power Query or DAX, verify every Sales[Productindex] exists in Products_Data[Productindex].",
                "Repeat for Storeindex → storelocations and Salesteamindex → Salesteams.",
            ],
            prerequisites=["validate-01"],
            expected="No unmatched keys (0 orphan rows).",
            mistakes=["Leading zeros stripped in CSV — keep Productindex as whole number"],
        )
    )
    steps.append(
        step(
            "validate-03",
            "validate-data",
            3,
            "Date coverage",
            "Understand the sample period.",
            [
                "Date Table covers 2020-01-01 through 2020-05-31 (152 days).",
                "Sales dates should fall inside this range.",
            ],
            prerequisites=["validate-02"],
            expected="min(Sales[Sales Date]) ≥ 2020-01-01 and max ≤ 2020-05-31.",
        )
    )
    steps.append(
        step(
            "validate-04",
            "validate-data",
            4,
            "Unmatched sales check",
            "Document blank keys.",
            ["Sort Sales columns for null Productindex/Storeindex/Salesteamindex — expect none."],
            prerequisites=["validate-03"],
            expected="No blank foreign keys in Sales.",
        )
    )

    rels = load_json("relationships.json")
    for idx, rel in enumerate(rels, start=1):
        steps.append(
            step(
                f"rel-{idx:02d}",
                "relationships",
                idx,
                f"{rel['fromTable']}.{rel['fromColumn']} → {rel['toTable']}.{rel['toColumn']}",
                "Create one active many-to-one relationship with single-direction filter from dimension to Sales.",
                [
                    "Model view → drag from Sales foreign key to dimension primary key.",
                    f"From: **{rel['fromTable']}**[{rel['fromColumn']}]",
                    f"To: **{rel['toTable']}**[{rel['toColumn']}]",
                    "Cardinality: Many-to-one (*:1).",
                    "Cross-filter direction: Single (dimension filters Sales).",
                    "Leave relationship **active**.",
                ],
                prerequisites=["validate-04"] if idx == 1 else [f"rel-{idx-1:02d}"],
                expected="Relationship line shows 1 on dimension side, * on Sales.",
                checklist=["Active", "Single direction from dimension"],
            )
        )

    steps.append(
        step(
            "date-01",
            "date-controls",
            1,
            "Mark the date table",
            "Enable time intelligence on Date Table.",
            [
                "Select **Date Table** in the Fields pane.",
                "Table tools → Mark as date table → choose column **Date**.",
            ],
            prerequisites=["rel-04"],
            expected="Date Table shows date table icon.",
        )
    )
    steps.append(
        step(
            "date-02",
            "date-controls",
            2,
            "Sort month labels",
            "Chronological month order on visuals.",
            [
                "Select Date Table[Month Short].",
                "Column tools → Sort by column → **Month Number**.",
                "Repeat: Week label columns sorted by WeeknYear if used on axis.",
            ],
            prerequisites=["date-01"],
            expected="Months order Jan–May, not alphabetically.",
        )
    )
    steps.append(
        step(
            "date-03",
            "date-controls",
            3,
            "Create D/W/M field parameter",
            "Match the reference slicer that drives axis grain.",
            [
                "Modeling → New parameter → Fields.",
                "Add fields: Date Table[Date] (Day), Date Table[WeeknYear] (Week), Date Table[Month Short] (Month).",
                "Name the parameter **Date M-W-D** (rename display column to `Date M-W-D` and order column `Date M-W-D Order`).",
                "Do **not** import Date_M-W-D.csv expecting parameter metadata — that CSV is only a helper lookup.",
            ],
            prerequisites=["date-02"],
            reference_notes="Reference binds charts to the field parameter, not bookmark-only grain switching.",
            expected="Slicer parameter with three values orders Day < Week < Month.",
        )
    )
    steps.append(
        step(
            "date-04",
            "date-controls",
            4,
            "Hide helper columns",
            "Reduce clutter.",
            ["Hide technical columns on Date Table used only for sorting (Month Number, etc.) except those needed on visuals."],
            prerequisites=["date-03"],
            expected="Students can still sort months correctly.",
            status="pending_desktop",
        )
    )

    measures = topo_sort_measures(measure_catalog())
    m_order = 1
    batch: list[dict] = []
    batch_names: list[str] = []

    def flush_measures() -> None:
        nonlocal m_order, batch, batch_names
        if not batch:
            return
        steps.append(
            step(
                f"measure-{m_order:02d}",
                "measures",
                m_order,
                f"Measures: {', '.join(batch_names[:3])}{'…' if len(batch_names) > 3 else ''}",
                "Create DAX measures in dependency order.",
                [
                    "Modeling → New table → name it `# Measures` (hide later).",
                    "New measure for each formula below (home table `# Measures` unless noted).",
                    "Set format strings where specified in checklist.",
                ],
                prerequisites=["date-03"] if m_order == 1 else [f"measure-{m_order-1:02d}"],
                dax=batch,
                expected="Measures compile without errors.",
                checklist=[f"`{n}` returns values" for n in batch_names],
                reference_notes=(
                    "Total Orders sums Order qty (units sold), matching the reference label — not distinct order IDs."
                    if "Total Orders" in batch_names
                    else ""
                ),
            )
        )
        m_order += 1
        batch = []
        batch_names = []

    for block in measures:
        batch.append(dax_block(block["table"], block["name"], block["expression"]))
        batch_names.append(block["name"])
        if len(batch) >= 6:
            flush_measures()
    flush_measures()

    last_measure_step = f"measure-{m_order-1:02d}" if m_order > 1 else "date-03"

    def img_ref(path: str, title: str) -> list[dict]:
        return [{"src": path, "caption": title, "alt": title, "role": "result"}]

    # Page / slicers / visuals — concise actionable steps
    visual_defs: list[dict] = [
        {
            "id": "page-01",
            "stageId": "page-slicers",
            "order": 1,
            "title": "Page size and header",
            "objective": "Match 1280×780 canvas.",
            "actions": [
                "View → Page view → 16:9.",
                "Format page → Page size → Custom 1280×780.",
                "Add title text box: Executive Sales.",
            ],
            "prerequisites": [last_measure_step],
            "images": img_ref("steps/02-slicers.png", "Page layout reference"),
        },
        {
            "id": "page-02",
            "stageId": "page-slicers",
            "order": 2,
            "title": "Store slicer",
            "objective": "Filter by store name.",
            "actions": [
                "Insert → Slicer → Field **storelocations[name]**.",
                "Rename header Stores; slicer style dropdown; position top-right.",
            ],
            "prerequisites": ["page-01"],
            "visual": {"visualType": "slicer", "fields": ["storelocations[name]"]},
            "images": img_ref("visuals/cd602ccaa356b4004e2b.png", "Store slicer"),
        },
        {
            "id": "page-03",
            "stageId": "page-slicers",
            "order": 3,
            "title": "Sales Team slicer",
            "objective": "Filter by team.",
            "actions": ["Slicer on **Salesteams[Sales Team]**.", "Place beside Stores slicer."],
            "prerequisites": ["page-02"],
            "visual": {"visualType": "slicer", "fields": ["Salesteams[Sales Team]"]},
            "images": img_ref("visuals/63a3d9016ba0074454a5.png", "Sales Team slicer"),
        },
        {
            "id": "page-04",
            "stageId": "page-slicers",
            "order": 4,
            "title": "Product slicer",
            "objective": "Filter products.",
            "actions": ["Slicer on **Products_Data[Product Name]**."],
            "prerequisites": ["page-03"],
            "visual": {"visualType": "slicer", "fields": ["Products_Data[Product Name]"]},
            "images": img_ref("visuals/60e1b53b36dd96759bb6.png", "Product slicer"),
        },
        {
            "id": "kpi-01",
            "stageId": "kpi-bars",
            "order": 1,
            "title": "Total Sales card",
            "objective": "Primary revenue KPI.",
            "actions": [
                "Card visual → Field **Total Sales**.",
                "Add adjacent card or callout with **Formatted KPI % WoW** for arrow comparison.",
            ],
            "prerequisites": ["page-04"],
            "visual": {"visualType": "card", "fields": ["Total Sales", "Formatted KPI % WoW"]},
            "images": img_ref("visuals/2ed267463a11685d300a.png", "Total Sales card"),
        },
        {
            "id": "kpi-02",
            "stageId": "kpi-bars",
            "order": 2,
            "title": "Profit Margin % card",
            "objective": "Margin KPI with comparisons.",
            "actions": ["Card → **Profit Margin %**.", "Format as percentage."],
            "prerequisites": ["kpi-01"],
            "visual": {"visualType": "card", "fields": ["Profit Margin %"]},
            "images": img_ref("visuals/f62b86a11712469079d9.png", "Profit Margin card"),
        },
        {
            "id": "kpi-03",
            "stageId": "kpi-bars",
            "order": 3,
            "title": "Units Sold card (measure: Total Orders)",
            "objective": "Show units sold; reference PBIX titles this Total Orders.",
            "actions": [
                "Create measure **Total Orders** = `SUM(Sales[Order qty])` (already in measure steps).",
                "Card → **Total Orders**; set visual title to **Units Sold** for clarity.",
                "Reference report keeps the Total Orders label — both refer to the same units-sold logic.",
            ],
            "prerequisites": ["kpi-02"],
            "visual": {"visualType": "card", "fields": ["Total Orders"]},
            "images": img_ref("visuals/4bd08ae993b0e8332530.png", "Units sold card"),
        },
        {
            "id": "kpi-04",
            "stageId": "kpi-bars",
            "order": 4,
            "title": "Target achievement card",
            "objective": "Monthly target %.",
            "actions": [
                "Card → **Target vs Previous month**; format as percentage.",
                "Target basis: prior-month sales + 20% (see Target +0.2 of Previous month).",
            ],
            "prerequisites": ["kpi-03"],
            "visual": {"visualType": "card", "fields": ["Target vs Previous month"]},
            "images": img_ref("visuals/cbe9a324a9d03737a60d.png", "Target card"),
        },
        {
            "id": "kpi-05",
            "stageId": "kpi-bars",
            "order": 5,
            "title": "Cost vs profit bar",
            "objective": "100% stacked composition bar.",
            "actions": [
                "Insert → 100% stacked bar chart.",
                "Values: **Total Cost**, **Total Profit**.",
                "Data labels: **cost formatted**, **profit formatted**.",
            ],
            "prerequisites": ["kpi-04"],
            "visual": {"visualType": "hundredPercentStackedBarChart", "fields": ["Total Cost", "Total Profit"]},
            "images": img_ref("steps/04-profit-bar.png", "Cost vs profit bar"),
        },
        {
            "id": "kpi-06",
            "stageId": "kpi-bars",
            "order": 6,
            "title": "Target remainder bar",
            "objective": "Achievement vs gap bar (not cost/profit).",
            "actions": [
                "Use **Target vs Previous month** and **Target Diff** in a separate bar visual.",
                "Format colors to match reference achievement/remainder story.",
            ],
            "prerequisites": ["kpi-05"],
            "visual": {"visualType": "clusteredColumnChart", "fields": ["Target vs Previous month", "Target Diff"]},
            "images": img_ref("visuals/5e13584087e05e680a11.png", "Target bar"),
        },
        {
            "id": "trend-01",
            "stageId": "trend-settings",
            "order": 1,
            "title": "Sales trend line",
            "objective": "Line chart with conditional color.",
            "actions": [
                "Line chart → Axis: **Date M-W-D** parameter.",
                "Values: **Total Sales**.",
                "Line color → fx → **Color Formatting Line Chart**.",
            ],
            "prerequisites": ["kpi-06"],
            "visual": {"visualType": "lineChart", "fields": ["Total Sales", "Color Formatting Line Chart"]},
            "images": img_ref("steps/05-trend-chart.png", "Sales trend"),
        },
        {
            "id": "trend-02",
            "stageId": "trend-settings",
            "order": 2,
            "title": "Percentile slicers",
            "objective": "Trend band thresholds.",
            "actions": [
                "Slicers on **Higher Percentile[Higher Percentile]** and **Lower Percentile[Lower Percentile]**.",
            ],
            "prerequisites": ["trend-01"],
            "visual": {"visualType": "slicer", "fields": ["Higher Percentile", "Lower Percentile"]},
            "images": img_ref("visuals/3322e1f65b8d195b9cd7.png", "Percentile slicers"),
        },
        {
            "id": "toast-01",
            "stageId": "toast",
            "order": 1,
            "title": "Add HTML Content visual",
            "objective": "Toast host visual.",
            "actions": ["Insert → HTML Content.", "Place full width near top; send to front."],
            "prerequisites": ["trend-02"],
            "visual": {"visualType": "htmlContent443BE3AD55E043BF878BED274D3A6855", "fields": []},
            "images": img_ref("steps/06-toast.png", "Toast placement"),
        },
        {
            "id": "toast-02",
            "stageId": "toast",
            "order": 2,
            "title": "Bind toast measures",
            "objective": "HTML content + stylesheet.",
            "actions": [
                "Values well → **Toast Notification**.",
                "Format → Stylesheet → **Toast CSS** (fix box-shadow closing parenthesis).",
            ],
            "prerequisites": ["toast-01"],
            "visual": {"visualType": "htmlContent443BE3AD55E043BF878BED274D3A6855", "fields": ["Toast Notification", "Toast CSS"]},
            "images": img_ref("visuals/d229beaccea875451039.png", "HTML Content bindings"),
            "reference_notes": TOAST_CSS_FIXED,
        },
        {
            "id": "toast-03",
            "stageId": "toast",
            "order": 3,
            "title": "Filter trigger tests",
            "objective": "Toast follows slicers, not targets.",
            "actions": [
                "No filters → no toast.",
                "Single product / store / team → singular label.",
                "Multiple values → plural label; products take priority over store/team in _Filter DAX.",
                "Replay animation by changing filters after toast hides (~3.5s).",
            ],
            "prerequisites": ["toast-02"],
            "images": img_ref("steps/06-toast.png", "Toast visible state"),
            "status": "pending_desktop",
        },
        {
            "id": "interact-01",
            "stageId": "interactions",
            "order": 1,
            "title": "Bookmarks and buttons",
            "objective": "Panel states for settings/calendar/trend.",
            "actions": [
                "View → Bookmarks → add bookmarks with these **display names** (reference PBIX):",
                "**Top Selected**, **Bottom Selected**, **Show date**, **Hide date**, **--Show settings**, **--Hide settings**, **( pag2 show calender**, **( page2 close calende**.",
                "For each bookmark, update **Data** → uncheck Data and capture **Selected visuals** visibility only where needed.",
                "Assign action buttons (settings / calendar / trend PNG assets) to **Bookmark** actions pointing to the matching bookmark.",
            ],
            "prerequisites": ["toast-03"],
            "reference_notes": "Bookmark internal ids: Bookmark84783c888e83915b339c (Top Selected), Bookmarkbd3388c53d8a33925955 (Bottom Selected), Bookmark6f74f6ce42b922585c0c (Show date), Bookmarka7b70c0ebc10c14b0289 (Hide date), Bookmarkbdcb9f803a97139d28d8 (--Show settings), Bookmarkc3839291ca6ed7324c15 (--Hide settings), Bookmark42a06dc2030c00a0eb6c (calendar show), Bookmark22388b10992648900480 (calendar close).",
            "status": "pending_desktop",
        },
        {
            "id": "final-01",
            "stageId": "final-checks",
            "order": 1,
            "title": "Unfiltered KPI baseline",
            "objective": "Match documented aggregates.",
            "actions": [
                "Clear slicers.",
                "Compare measures to `expected-results.json` → `displayCurrency` (2dp, reconciled profit).",
            ],
            "prerequisites": ["interact-01"],
            "expected": "See expected-results.json displayCurrency block.",
            "checklist": ["Measures compile", "Refresh succeeds", "Profit = Sales − Cost at display precision"],
        },
        {
            "id": "final-02",
            "stageId": "final-checks",
            "order": 2,
            "title": "Save and reopen",
            "objective": "Persistence check.",
            "actions": ["Save PBIX, close Desktop, reopen and refresh."],
            "prerequisites": ["final-01"],
            "status": "pending_desktop",
        },
    ]

    for vd in visual_defs:
        steps.append(
            step(
                vd["id"],
                vd["stageId"],
                vd["order"],
                vd["title"],
                vd["objective"],
                vd["actions"],
                prerequisites=vd.get("prerequisites"),
                visual=vd.get("visual"),
                images=vd.get("images"),
                expected=vd.get("expected", vd["objective"]),
                checklist=vd.get("checklist"),
                reference_notes=vd.get("reference_notes", ""),
                status=vd.get("status", "verified"),
            )
        )

    return steps


def build_stages() -> list[dict]:
    return [
        {"id": "setup", "order": 1, "title": "Setup", "summary": "Tools, downloads, blank PBIX"},
        {"id": "import", "order": 2, "title": "Import data", "summary": "CSV imports with exact table names"},
        {"id": "validate-data", "order": 3, "title": "Validate data", "summary": "Counts, keys, dates"},
        {"id": "relationships", "order": 4, "title": "Model relationships", "summary": "Four active M:1 relationships"},
        {"id": "date-controls", "order": 5, "title": "Date controls", "summary": "Date table, sort, D/W/M parameter"},
        {"id": "measures", "order": 6, "title": "Measures", "summary": "DAX in dependency order"},
        {"id": "page-slicers", "order": 7, "title": "Page and slicers", "summary": "Canvas and filters"},
        {"id": "kpi-bars", "order": 8, "title": "KPI cards and bars", "summary": "KPIs, cost/profit and target bars"},
        {"id": "trend-settings", "order": 9, "title": "Trend and settings", "summary": "Trend line and percentile controls"},
        {"id": "toast", "order": 10, "title": "Toast", "summary": "HTML Content notification"},
        {"id": "interactions", "order": 11, "title": "Interactions", "summary": "Bookmarks and buttons"},
        {"id": "final-checks", "order": 12, "title": "Final checks", "summary": "Validate, save, export"},
    ]


def write_supporting_docs() -> None:
    if not (LAB / "expected-results.json").is_file():
        raise SystemExit("Run compute-expected-results.py before build-executive-sales-workshop.py")
    (LAB / "data-dictionary.md").write_text(
        "# Data dictionary\n\n"
        "| Table | File | Notes |\n|-------|------|-------|\n"
        "| Sales | Sales.csv | Fact; 20,000 rows |\n"
        "| Date Table | Date_Table.csv | Mark as date table; 152 days |\n"
        "| Products_Data | Products_Data.csv | Product dimension |\n"
        "| storelocations | storelocations.csv | Store dimension |\n"
        "| Salesteams | Salesteams.csv | Team dimension |\n"
        "| Higher Percentile | Higher_Percentile.csv | Disconnected percentile lookup |\n"
        "| Lower Percentile | Lower_Percentile.csv | Disconnected percentile lookup |\n"
        "| Date M-W-D | Date_M-W-D.csv | Helper only — recreate field parameter in Desktop |\n",
        encoding="utf-8",
    )
    if not (LAB / "csv-import.md").is_file():
        raise SystemExit("Run generate-csv-import-queries.py before build-executive-sales-workshop.py")


def write_student_kit(measures: list[dict]) -> None:
    kit_dir = LAB / "student-kit"
    kit_dir.mkdir(exist_ok=True)
    (kit_dir / "README.md").write_text(
        "# Executive Sales Toast — student kit\n\n"
        "Use with the JobReady guided lab. Import CSVs only; do not use author Excel paths.\n",
        encoding="utf-8",
    )
    zip_path = LAB / "student-kit.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in LAB.rglob("*"):
            if path.is_dir():
                continue
            rel = path.relative_to(LAB)
            if rel.parts[0] in {"visuals", "steps"} or rel.name.endswith(".png"):
                continue
            if rel.name in {"student-kit.zip", "datasets.zip"}:
                continue
            zf.write(path, arcname=f"executive-sales-toast-lab/{rel.as_posix()}")


def main() -> None:
    manifest = load_json("manifest.json")
    stages = build_stages()
    steps = build_steps()
    expected = json.loads((LAB / "expected-results.json").read_text(encoding="utf-8"))
    content = {
        "contentVersion": CONTENT_VERSION,
        "reportId": "executive-sales-toast",
        "title": "Executive Sales Report — Toast Notification",
        "learningOutcomes": [
            "Import CSV star-schema data with Power Query",
            "Model relationships and a marked date table",
            "Author DAX for KPIs, targets, and toast alerts",
            "Recreate the reference dashboard layout in Power BI Desktop",
        ],
        "prerequisites": ["Basic Power BI Desktop familiarity"],
        "testedDesktopVersion": "Power BI Desktop 2024–2025 (HTML Content 1.2.1.17)",
        "canonicalPbixSha256": manifest.get("sourcePbixSha256"),
        "excludedMeasures": EXCLUDED_MEASURES,
        "intentionalDifferences": [
            {
                "topic": "Toast CSS",
                "detail": "Students use corrected box-shadow syntax; reference PBIX measure omits a closing parenthesis.",
            },
            {
                "topic": "Units Sold vs Total Orders",
                "detail": "DAX measure remains Total Orders (= SUM of Order qty). Students should title the card Units Sold; reference PBIX label says Total Orders.",
            },
            {
                "topic": "CSV import path",
                "detail": "Students use Csv.Document on packaged CSVs; author Excel M is reference-only.",
            },
        ],
        "stages": stages,
        "steps": steps,
        "expectedResults": {
            **expected,
            "dateRange": ["2020-01-01", "2020-05-31"],
            "desktopVerification": "pending",
        },
        "downloads": [
            {"label": "Datasets (CSV)", "path": "datasets.zip"},
            {"label": "Student kit", "path": "student-kit.zip"},
            {"label": "Build guide (Markdown)", "path": "build-guide.md"},
            {"label": "Data dictionary", "path": "data-dictionary.md"},
            {"label": "CSV import (M)", "path": "csv-import.md"},
        ],
    }
    (LAB / "workshop-content.json").write_text(json.dumps(content, indent=2), encoding="utf-8")
    write_supporting_docs()
    write_student_kit(measure_catalog())
    subprocess.run(
        ["node", "--experimental-strip-types", str(ROOT / "scripts" / "export-workshop-markdown.mjs")],
        check=True,
        cwd=ROOT,
    )
    print(f"Wrote workshop-content.json ({len(steps)} steps)")


if __name__ == "__main__":
    main()
