# PR #24 release verification and pilot deploy

**Release code SHA:** `53363b8` (pending CI [40075071754](https://github.com/gaganpasupuleti/job-ready-platform/actions/runs/40075071754))  
**Prior syllabus SHA:** `dd289ff` — CI [40070858460](https://github.com/gaganpasupuleti/job-ready-platform/actions/runs/40070858460)  
**Branch:** `feat/roadmap-ui-clean`  
**PR:** https://github.com/gaganpasupuleti/job-ready-platform/pull/24  

## Pilot limitations (accepted for release)

1. **data-analyst:** “VLOOKUP / HLOOKUP” subtopic has **no incoming canvas edge** after upstream sanitize; reachable via **topic search + article**. No invented edge. **Follow-up:** optional curated graph correction.
2. **code-review articles:** upstream markdown not keyed by `*@{nodeId}.md`; sampled audit **missing** for one node. UI shows truthful unavailable content. **Follow-up:** mapping or upstream alignment.
3. **Article coverage:** one readable node sampled per slug only — **not** full corpus coverage (**10 375** nodes unchecked by sampling).

## Verification matrix

| # | Check | Status | Evidence |
|---|--------|--------|----------|
| 1 | **CI on release SHA** | **In progress** | Run [40075071754](https://github.com/gaganpasupuleti/job-ready-platform/actions/runs/40075071754) for `53363b8` |
| 2 | **Special maps + data-analyst** | **Completed** | `docs/ci-evidence/special-roadmap-maps-1ebbd48.json`; e2e `roadmap-data-analyst-semantic.spec.ts`; screenshots `frontend/e2e/artifacts/special-roadmap-maps/` |
| 3 | **Article audit (sampled)** | **Completed** | `docs/ci-evidence/article-audit-post-syllabus-summary.json` — **92/93** OK, **1** missing (`code-review`) |
| 4 | **Preview surface smoke** | **Completed** | `docs/ci-evidence/release-smoke-preview-post-syllabus-local.json` — **3/3** |
| 5 | **Preview AUTH-01 (registration closed)** | **Completed** | `docs/ci-evidence/release-smoke-preview-auth-local.json` — pre-provisioned accounts + production bundle; fixes prior full-script failure on closed registration |
| 6 | **Contrast / UI** | **Completed** | `docs/ci-evidence/contrast-local-compositing-summary.json`; `frontend/e2e/artifacts/ui-cohesion/after/` |
| 7 | **Syllabus bundle** | **Completed** | `docs/ROADMAP_SYLLABUS_CONTENT.md`; default root `backend/app/data/roadmap-syllabus/roadmaps` |

## Railway (production)

| Item | Value |
|------|--------|
| Frontend URL | https://frontend-production-f65c0.up.railway.app |
| Backend URL | https://backend-production-a0c9.up.railway.app |
| Build | `VITE_API_BASE_URL` → backend origin; syllabus in backend image; `ROADMAP_CONTENT_ROOT` unset → bundled default |
| Rollback | Redeploy prior Railway deployment IDs for frontend + backend services (record before deploy) |

## Post-merge live verification

_To be filled after deploy:_ deployment IDs, merge SHA, smoke results.
