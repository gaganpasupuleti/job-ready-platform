# Power BI learning space — audit handoff

**Branch:** `feat/power-bi-reports-lab`  
**Scope:** Frontend-only feature (static assets under `frontend/public/reports/`). No backend API for reports yet.

## Product intent

Students should **rebuild** the *Executive Sales Report — Toast Notification* in Power BI Desktop using:

- Downloadable **datasets** (CSV / zip)
- Documented **model relationships**
- Copy-paste **DAX** and **Power Query (M)**
- A **numbered build path** with canvas screenshots (not a locked embed)

Optional: static **preview** image; optional live embed via env var (not required for lab).

## Routes

| Path | Component | Purpose |
|------|-----------|---------|
| `/reports` | `PowerBiReportsPage` | Catalog |
| `/reports/:reportId/preview` | `PowerBiReportPreviewPage` | PNG/PDF preview or embed fallback |
| `/reports/:reportId/lab` | `PowerBiReportLabPage` | Learning studio |
| `/reports/:reportId` | `PowerBiReportPage` | Live iframe when `VITE_POWERBI_*_EMBED_URL` set |

**Nav:** `Reports` (primary); **More → Career → Power BI reports**.

## Catalog config

- `frontend/src/config/powerBiReports.ts` — report id `executive-sales-toast`, `labPath`, preview URLs, env overrides.

## Lab assets (`frontend/public/reports/executive-sales-toast-lab/`)

| Asset | Description |
|-------|-------------|
| `data/*.csv` | 8 tables extracted from `.pbix` (Sales ~20k rows) |
| `datasets.zip` | All CSVs bundled |
| `manifest.json` | Table list, counts, canvas rect metadata |
| `relationships.json` / `relationships.md` | 4 star-schema relationships + Mermaid |
| `dax-measures.json` | 52 measures |
| `power-query.json` | 6 M queries (still reference original Excel paths) |
| `build-steps.json` + `steps/*.png` | 6-step build path screenshots |
| `build-guide.md` | Long-form rebuild doc |
| `canvas-reference.png` | Cropped report canvas from preview PNG |
| `visuals/*.png` | Per-visual crops (advanced section only) |

**Preview / reference**

- `frontend/public/reports/executive-sales-toast.png` — full-window capture for preview + crop source
- `frontend/public/reports/Exceutive Sales Report - Toast Notifictaion.pbix` — reference download

## Tooling

- `frontend/scripts/extract-pbix-lab.py` — regenerate lab from `.pbix` (+ optional `--preview` PNG). Requires `pbixray` in backend venv.
- `frontend/scripts/sync-report-pdf.ps1` — copy PDF export from Downloads into `public/reports/`

## Env vars (`frontend/.env.example`)

- `VITE_POWERBI_EXECUTIVE_SALES_EMBED_URL` — optional live embed
- `VITE_POWERBI_EXECUTIVE_SALES_PREVIEW_URL` / `_PREVIEW_IMAGE_URL` / `_DOWNLOAD_URL` — optional overrides

## Known gaps (for auditors)

1. **No production deploy** in this PR — verify Railway frontend build size (~4MB `public/reports`).
2. **No PDF** — preview uses PNG unless user exports PDF.
3. **No embed URL** — live page shows setup unless env set.
4. **M queries** still point at author Excel paths; students should import **CSVs**.
5. **No backend** — no auth-gated downloads, analytics, or R2 like Library.
6. **No progress UI** — lab is static; no checklist persistence.
7. **CORS** — `backend/app/core/config.py` adds 5174 for alternate Vite port (dev only).

## Suggested audit checks

- [ ] `npm run build` (frontend) succeeds with new pages
- [ ] `/reports/executive-sales-toast/lab` loads `build-steps.json` and images
- [ ] `datasets.zip` downloads and CSVs open
- [ ] Preview page shows PNG (not instruction card)
- [ ] No secrets in `.env` committed
- [ ] `extract-pbix-lab.py` reruns cleanly after `.pbix` change

## Key files (code)

```
frontend/src/pages/reports/*.tsx
frontend/src/features/reports/reportAssets.ts
frontend/src/config/powerBiReports.ts
frontend/src/routes/index.tsx
frontend/src/components/navigation/navConfig.ts
```
