# Power BI workshop — audit finding → fix register

| Finding | Fix |
|---------|-----|
| Disconnected lab sections, no progress | Guided UI with 4 views, 12 stages, 50 steps, localStorage progress keyed by `reportId` + `contentVersion` |
| Students told to repoint Excel M to CSV folder | `csv-import.md`, workshop import steps use `Csv.Document` + `DataFolder` parameter; author M labeled reference-only in Resources |
| Mermaid ER diagram reversed | `extract-pbix-lab.py` draws dimension `\|\|--o{` Sales |
| Visual parser missed grouped coordinates | `parentGroupName` chain resolved to absolute x/y; legacy `Report/Layout` fallback when no page JSON visuals |
| Zero-visual false success | Extractor exits non-zero when no visuals parsed |
| Hardcoded crop rect only | `--canvas-rect` JSON override; provenance in `manifest.json` |
| Toast tied to wrong triggers in copy | Steps document slicer-driven toast; product → store → team priority in DAX |
| Malformed Toast CSS | Documented intentional fix (box-shadow closing parenthesis) in `intentionalDifferences` |
| Missing measures on broken tables | `ranking_*`, scatter percentile measures excluded with reasons |
| Total Orders semantics unclear | Documented as sum of `Order qty` (units sold) matching reference label |
| build-steps.json only 6 steps | `workshop-content.json` canonical curriculum + generated Markdown download |
| No student kit | `student-kit.zip` + manifests with SHA-256, extractor 2.1.0 |
| PBIX byte mismatch (HEAD vs working tree) | Semantic identity proven; WT `664ecd9d…` archived under `docs/evidence/`; canonical aligned to HEAD `6dad3a32…` |
| Financial KPI prose mismatch | `compute-expected-results.py` + reconciliation assert; profit = rounded sales − rounded cost |
| Wrong regenerate paths in handoff | `frontend/scripts/regenerate-power-bi-lab.ps1` uses `frontend/public/reports/` |

## Desktop verification (pending)

- [ ] Blank PBIX end-to-end rebuild
- [ ] Toast animation replay on filter changes
- [ ] Bookmark / panel buttons
- [ ] D/W/M field parameter axis switching
