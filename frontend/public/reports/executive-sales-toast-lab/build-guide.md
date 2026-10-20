# Rebuild: Executive Sales Report (with toast notification)

Use the **datasets**, **Power Query**, and **DAX** blocks in this lab to recreate the dashboard yourself in Power BI Desktop.

## What you get

| Block | Files |
|-------|--------|
| **Data** | `data/*.csv` or `datasets.zip` (Sales, Products, teams, stores, date tables) |
| **Power Query (M)** | `power-query.json` — import logic (point Excel paths to your CSV folder) |
| **DAX** | `dax-measures.json` — 52 measures including KPI cards, WoW/MoM, toast HTML/CSS |
| **Report shell** | Download the `.pbix` from Reports → use as reference or start blank |

## Step 1 — Load data

1. Open **Power BI Desktop** → **Get data** → **Text/CSV**.
2. Import each CSV from `data/`:
   - `Sales.csv` (fact table, ~20k rows)
   - `Products_Data.csv`, `Salesteams.csv`, `storelocations.csv`
   - `Date_Table.csv`, `Date_M-W-D.csv`, percentile helper tables
3. Set column types to match the M expressions in **power-query.json** (dates, integers for index keys).

**Relationships (star schema):** see **`relationships.md`** in this folder (table + diagram) or the **Model relationships** section in the Build lab UI.

- `Sales[Salesteamindex]` → `Salesteams[Salesteamindex]`
- `Sales[Storeindex]` → `storelocations[Storeindex]`
- `Sales[Productindex]` → `Products_Data[Productindex]`
- `Sales[Sales Date]` → `Date Table[Date]`

## Step 2 — Date table

1. Mark **Date Table** as a **date table** (Model view → table properties).
2. Add calculated columns / tables for week/month labels if needed (see **Date M-W-D** CSV).
3. Measures like `Total Sales PM` use `PARALLELPERIOD('Date Table'[Date], -1, MONTH)`.

## Step 3 — Core measures (# Measures table)

Create a **# Measures** table (enter data → single column, or use a blank table). Add measures in this order:

1. **Total Sales** — `SUMX(Sales, Sales[Order qty] * Sales[unit price])`
2. **Total Cost** — `SUMX(Sales, Sales[Order qty] * Sales[unit cost])`
3. **Total Profit** — `[Total Sales] - [Total Cost]`
4. **Profit Margin %** — `DIVIDE([Total Profit], [Total Sales])`
5. **Total Orders** — `SUM(Sales[Order qty])`

Copy remaining measures from **dax-measures.json** (WoW/MoM diffs, target %, formatted KPI strings, toast notification).

## Step 4 — Page layout (1280×780)

Use **Visuals (with snips)** in the Build lab: each card shows a **cropped screenshot**, visual type, fields, and how to insert it in Power BI.

Summary:

| Area | Type | Notes |
|------|------|--------|
| Header | Text + slicers | Stores, Sales Team, Products |
| KPI row | Cards | Total Sales, Profit Margin %, Total Orders, % of Target, Avg Daily Sales |
| Trend | Line chart | Total Sales over time; D/W/M bookmarks |
| Toast | HTML Content visual | **Toast Notification** + **Toast CSS** measures |

## Step 5 — Interactions & bookmarks

1. Slicers filter all visuals on the page.
2. Bookmarks in the original report toggle: date granularity (D/W/M), settings panel, month selection.
3. Recreate **Selection** → **Edit interactions** so KPI cards cross-filter the line chart as in the reference.

## Step 6 — Toast notification block

1. Insert the **HTML Content** custom visual (same as source report).
2. Bind **Toast Notification** (measure returning HTML) and **Toast CSS** (measure returning stylesheet text).
3. Test with a low target % or negative WoW so the toast appears.

## Step 7 — Publish & validate

1. Compare numbers to the CSV aggregates (e.g. sum of `Order qty * unit price` in Excel).
2. Export **PDF** to `frontend/public/reports/executive-sales-toast.pdf` if you want an in-app static preview.

## Refresh lab assets

From repo root (requires `pbixray` in backend venv):

```bash
backend/.venv/Scripts/python.exe frontend/scripts/extract-pbix-lab.py \
  --pbix "frontend/public/reports/Exceutive Sales Report - Toast Notifictaion.pbix" \
  --out "frontend/public/reports/executive-sales-toast-lab"
```
