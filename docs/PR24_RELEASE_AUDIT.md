# PR #24 release verification (truthful status)

**Candidate SHA:** `dfa6eab`  
**Branch:** `feat/roadmap-ui-clean`  
**PR:** https://github.com/gaganpasupuleti/job-ready-platform/pull/24  
**Green CI (prior):** https://github.com/gaganpasupuleti/job-ready-platform/actions/runs/40032697907 (`67940fd`)  
**Green CI (this candidate):** _pending — https://github.com/gaganpasupuleti/job-ready-platform/actions (workflow run for `dfa6eab`)_  
**Not merged / not deployed.**

## Verification matrix

| # | Check | Status | Evidence |
|---|--------|--------|----------|
| 1 | **CI on HEAD** | **Pending** | Workflow run link after push to `feat/roadmap-ui-clean` |
| 2 | **Eight special-case maps** | **Completed (semantic) / product pending (data-analyst)** | Upstream + normalization: `docs/ci-evidence/special-roadmap-maps-1ebbd48.json`. **ux-design:** dangling edge targeted paragraph chrome. **data-analyst:** sanitized away layout-only edge from missing node `aopqiF0Svmpq94g6OQBX0` → subtopic `9sIP-jpNjtA1JPCBjTf-H` (“VLOOKUP / HLOOKUP”) — **no justified replacement edge**. Learner can still open topic via toolbar search + article API (`frontend/e2e/roadmap-data-analyst-semantic.spec.ts`; screenshots under `frontend/e2e/artifacts/special-roadmap-maps/`). **Product decision:** accept orphan subtopic on canvas vs. invest in curated edge correction. |
| 3 | **Authenticated article audit** | **Completed (sampled)** | Bundled syllabus from [developer-roadmap](https://github.com/kamranahmedse/developer-roadmap) @ `e906c5f60c2e72623a73cce4bea51153b319c0d8` — see `docs/ROADMAP_SYLLABUS_CONTENT.md` + `ROADMAP_SYLLABUS_MANIFEST.json`. Local audit: **93/93** graphs OK; **92/93** sampled articles OK; **1** missing (`code-review` — upstream files not keyed by node id). Summary: `docs/ci-evidence/article-audit-post-syllabus-summary.json`; rows: `frontend/e2e/artifacts/roadmap-catalog-audit.json`. File coverage: **10 454 / 10 468** readable nodes with `*@{id}.md` (`docs/ci-evidence/roadmap-article-file-coverage.json`). **Unchecked by sampling:** 10 375 readable nodes (one sample per slug). |
| 4 | **Preview build + release smoke** | **Completed (local live)** | `docs/ci-evidence/release-smoke-preview-post-syllabus-local.json` — production build + preview @4173, API @8000: **3/3** pass including **live roadmap article** (`release-smoke-preview.spec.ts`). |
| 5 | **Screenshots + contrast** | **Completed (mocked UI)** | `frontend/e2e/ui-cohesion.spec.ts` — artifacts `frontend/e2e/artifacts/ui-cohesion/after/` (Jobs, Library, Projects, header More/Account, roadmap catalog/article, mobile nav/sheet). **Contrast:** 42/42 probes **pass** ≥4.5:1 via alpha compositing (`docs/ci-evidence/contrast-local-compositing-summary.json`, `contrast-report.json`). Eight special maps: `frontend/e2e/artifacts/special-roadmap-maps/*-{desktop-1366,mobile-390}.png` (`roadmap-special-maps-screenshots.spec.ts`). |
| 6 | **Local SQL test failures explained** | **Completed** | `docs/ci-evidence/local-sql-test-failures.json` — requires SQL sandbox **:5433**; passes in CI with Docker services |

## Release decision

| Gate | Decision | Notes |
|------|----------|--------|
| Graph integrity + catalog E2E | **Ready** | Reused from `67940fd` / green CI 40032697907 where code unchanged; new commits add syllabus + contrast probe only |
| Article content | **Ready for pilot** | Bundled syllabus + reproducible import; truthful **code-review** gap documented |
| Preview smoke | **Ready** | Live article on preview with bundled content |
| Visual / contrast | **Ready** | Measured ratios on primary button + action link (both themes, hover) |
| data-analyst topic path | **Blocked on product** | No invented edge; navigation + article verified; canvas lacks incoming topic edge |

**Overall:** **Ship candidate after green CI on `dfa6eab`**, with explicit **product sign-off** on data-analyst orphan subtopic (or defer merge until decided). Do **not** treat single-sample article audit as full corpus coverage.

## Smoke identifiers (local verification)

| Item | Value |
|------|--------|
| Backend API | `http://127.0.0.1:8000` |
| Preview | `http://127.0.0.1:4173` |
| Syllabus commit | `e906c5f60c2e72623a73cce4bea51153b319c0d8` |
| Content root | `backend/app/data/roadmap-syllabus/roadmaps` (default when `ROADMAP_CONTENT_ROOT` unset) |
