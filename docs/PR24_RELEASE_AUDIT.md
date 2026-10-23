# PR #24 release verification (truthful status)

**Candidate SHA:** `1ebbd48`  
**PR:** https://github.com/gaganpasupuleti/job-ready-platform/pull/24  
**Green CI:** https://github.com/gaganpasupuleti/job-ready-platform/actions/runs/40028398164  
**Not merged / not deployed.**

Implementation work for cache integrity, normalization, and catalog E2E is **done on this SHA**. Release sign-off items below are **completed or pending** per evidence — nothing is marked complete without its acceptance check.

## Verification matrix (`1ebbd48`)

| # | Check | Status | Evidence |
|---|--------|--------|----------|
| 1 | **CI on HEAD** | **Completed** | Run [40028398164](https://github.com/gaganpasupuleti/job-ready-platform/actions/runs/40028398164): Frontend lint/unit/build ✓; Backend **345 passed**, 10 skipped; Playwright **145 passed**, 6 skipped, 0 failed |
| 2 | **Eight special-case maps** | **Completed** | `docs/ci-evidence/special-roadmap-maps-1ebbd48.json` (live upstream fetch + normalization). **ux-design:** resolved — dangling edge targeted paragraph chrome, not topic path. **data-analyst:** **unresolved** — subtopic “VLOOKUP / HLOOKUP” has no topic/subtopic incoming edges after sanitize. Dup-ID + **code-review** edgeless: deterministic remap / supported layout. CI browser: 85 clean + 1 edgeless + 7 sanitized (`docs/ci-evidence/roadmap-catalog-browser-40022619114.json` — same contract; re-validated on green CI run artifact from 40028398164 catalog upload) |
| 3 | **Authenticated article audit** | **Partial** | Graph: **93/93** integrity pass locally after audit CLI aligned with E2E (`frontend/scripts/audit-roadmap-catalog.mjs`). Articles: **0/93** sampled OK — all `missing` (no `ROADMAP_CONTENT_ROOT`). Summary: `docs/ci-evidence/article-audit-1ebbd48-local-summary.json`; rows: `article-audit-1ebbd48-local.json`. **Sampled:** 93 slugs × 1 node; **unchecked:** 10,375 / 10,468 readable topic nodes |
| 4 | **Preview build + release smoke** | **Partial** | Production `npm run build` + vite preview @4173 against local API (cache warmed): **2/3** pass — `docs/ci-evidence/release-smoke-preview-1ebbd48-local.json`. **Fail:** live roadmap article markdown (same content-root blocker) |
| 5 | **Screenshots + contrast** | **Partial** | CI artifact `ui-cohesion-after` on run 40028398164 (screenshots + `contrast-report.json`). **42/42** probes `unsupported_transparency` (semi-transparent stacks) — **no WCAG pass/fail ratio claimed**. Manual visual sign-off **pending** |
| 6 | **Local SQL test failures explained** | **Completed** | `docs/ci-evidence/local-sql-test-failures.json` — both fail without **:5433 SQL sandbox**; **pass in CI** with Docker services |

## Reused evidence (unchanged code path)

- Cache integrity regression: `backend/tests/test_roadmap_graph_cache.py` (13 tests on HEAD).
- Upstream CLI audit: 93 slugs in `docs/roadmap-upstream-graph-integrity.json`.
- Prior green catalog browser JSON remains valid for integrity totals; CI run **40028398164** re-uploaded catalog results with same 93/93 mounted classification.

## Remaining release blockers

1. **ROADMAP_CONTENT_ROOT** (or equivalent article sync) for meaningful article audit + preview article smoke locally and in hosted preview.
2. **Product sign-off** on **data-analyst** unresolved topic path (and general acceptance of 7 sanitized + 1 edgeless).
3. **Contrast/visual** — resolve or accept `unsupported_transparency` on primary buttons / action links (both themes).
4. **Optional:** run full `scripts/run-release-smoke.ps1` on a machine with Docker (Redis + SQL sandbox + content root) for end-to-end parity with CI.
