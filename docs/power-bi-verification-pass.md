# Power BI workshop — verification & packaging pass

**Date:** 2026-10-20  
**Branch:** `feat/power-bi-reports-lab`  
**Workshop content version:** `1.0.1`  
**Extractor:** `2.1.0`

## 1. Financial baseline reconciliation

**Root cause of the earlier mismatch:** prose rounded **Cost** to `$31,689,306` (or mixed precisions) while **Sales** and **Profit** used 2dp values. At 2dp, cost is **31689305.73**, not 31689306.00.

| | Formula | Value |
|---|---------|--------|
| Total Sales | Σ (Order qty × unit price) per row, `Decimal` | full: `44365028.02269119…` → display **44365028.02** |
| Total Cost | Σ (Order qty × unit cost) per row, `Decimal` | full: `31689305.73049371…` → display **31689305.73** |
| Total Profit | Sales − Cost (full precision) | full: `12675722.29219748…` → display **12675722.29** |
| Units sold | Σ Order qty | **110402** |

**Rounding policy:** `ROUND_HALF_UP` to 2 decimal places for dollar KPI checks; **display profit** = `money_round(Sales) − money_round(Cost)` so cards reconcile.

**Check:** `44365028.02 − 31689305.73 = 12675722.29` ✓  

Source of truth: `frontend/scripts/compute-expected-results.py` → `expected-results.json` (also embedded in `workshop-content.json`).

## 2. Canonical PBIX provenance

| Artifact | SHA-256 |
|----------|---------|
| **Canonical (HEAD = working tree after align)** | `6dad3a32cac39baaf4ea8ce998bc7dc09371b93a570a8092c2fb642bad6b8128` |
| Prior working-tree only (archived) | `664ecd9d026eae94951b6ec4f6d5ff504017f7b4bdb6bc4ea3ae4d6ca0deeff2` |

**Semantic comparison:** identical table list, 52 measures (same names), identical visual.json aggregate hash, same 8 bookmarks. 8-byte file size delta only.

**Why HEAD is canonical:** audited git blob; semantically same as the prior working-tree copy. Evidence: `docs/evidence/power-bi-pbix-provenance.json`, copy `docs/evidence/executive-sales-toast.pbix.at-HEAD.pbix`, archive `docs/evidence/executive-sales-toast.pbix.working-tree-664ecd9d026e.pbix`.

**Manifest:** `manifest.json` → `sourcePbixSha256` matches canonical HEAD hash.

## 3. Instructional completeness

- **51 steps** in `workshop-content.json` (includes `import-00` DataFolder + 8 full M imports from `csv-import-queries.json`).
- **DAX:** dependency-ordered batches from `dax-measures.json` (5 experimental measures excluded).
- **D/W/M:** field parameter step `date-03`; trend binds parameter axis in `trend-01`.
- **Bars:** `kpi-05` composition vs `kpi-06` target remainder.
- **Bookmarks:** `interact-01` lists display names + internal ids (`pending_desktop`).
- **Toast:** filter-driven DAX; CSS fix documented; `pending_desktop` for animation replay.
- **Units Sold:** card step uses student label; measure name remains `Total Orders`.

## 4. Screenshots

- Crops regenerated with group-coordinate resolution (0 mismatches on validation sample).
- `screenshot-audit.json` lists 9/9 key student images present.
- **Not claimed:** Desktop field-well config panes, bookmark state panes, toast animation.

## 5. Regeneration (correct paths)

Run from repo root:

```powershell
powershell -ExecutionPolicy Bypass -File frontend/scripts/regenerate-power-bi-lab.ps1
```

Or from `frontend`: `npm run regenerate:power-bi-lab`

Order: **extract** (does not touch `workshop-content.json`) → **compute-expected-results** → **generate-csv-import-queries** → **build-executive-sales-workshop** → **validate:power-bi-lab**.

**Wrong (old handoff):** `../public/reports/` from `frontend` points at repo-root `public/`, not `frontend/public/reports/`.

## 6. Frontend test results

| Check | Result |
|-------|--------|
| `npm run validate:power-bi-lab` | Pass (reconciliation assert) |
| `npm run test:unit` | Pass (26 tests) |
| `npm run build` | Pass |
| Playwright `power-bi-lab.spec.ts` | Mock-auth UI (see CI log / `e2e-artifacts/power-bi-lab/`) |

## 7. Desktop verification

**Not run in this pass.** Use `docs/power-bi-desktop-manual-test.md`. Workshop steps stay `pending_desktop` where applicable.

## 8. Audit register

See `docs/power-bi-workshop-fix-register.md`.
