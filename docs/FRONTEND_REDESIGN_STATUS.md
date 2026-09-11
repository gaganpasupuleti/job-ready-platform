# Frontend Redesign Status

Sprint ledger for JobReady Master Plan Phase 0 + Reliability Sprint 1.

| Field | Value |
|-------|-------|
| Workstream | dual (`feature/jobready-frontend-experience-v4`, `feature/jobready-learning-runtime-v4`) |
| Phase | Phase 0 + Sprint 1 reliability gates ? **Sprint 1 verification **GREEN** (2026-09-10)** |
| Base | FE: `origin/master` @ `7155ce0`; BE: includes `feb8d65` Alembic 014 tip (PR #3 supersedable by PR #4 ancestry) |
| Premium UI inspect | `feature/jobready-ui-skeleton-premium` @ `c217e4e` ? frontend-only; reuse tokens/shells/nav selectively later; **not** base for Sprint 1 |
| Master merge / deploy | **blocked** ? Gk owns release; do **not** merge to master or deploy from this stream |

## Sprint 1 scope

| Stream | Focus | Status |
|--------|-------|--------|
| Backend | ?26 A?E: auth bootstrap, mistakes, readiness, trusted completion, alembic 014 tip | **done** on learning-runtime (`5f59544` tip as of 2026-09-10) |
| Frontend | AUTH-01 cache isolation; primary nav reduction; honesty for readiness/mistakes UI | **done** + CI/AUTH hardening commits after `85a28c5` |

## Verification evidence (Sprint 1 close-out)

| Item | Evidence | SHA / ref |
|------|----------|-----------|
| Backend tip | PR #4 head | `5f59544152a33f84ed3357c7046e15649e00a4db` |
| Frontend tip (current tip) | PR #5 prior harden | `dba3ef712c2cc5c060759ffc3758af8a38ff0bc4` |
| Alembic 014 | Present on PR #4 via `feb8d65`; **do not double-merge PR #3** into master after #4 | `014_phase12_listing_type` |
| Mistake concurrency | `mistake_source_events` unique constraint + `test_mistake_concurrent_same_event_does_not_double_count` | migration `015_mistake_source_events` on BE branch |
| AUTH-01 | Cache clear on login/register/logout; private queryKeys scoped; 401 clears cache; cross-tab storage listener; failed logout still clears | FE `useAuth` + `api/client` + `e2e/auth.spec.ts` |
| Playwright (historical red) | PR #5 @ `85a28c5`: hub path progress + AI RAG smoke; PR #4 @ `ef188d5`: logout navigation race | Fixed in follow-up commits; re-run CI required |
| Integration | Local worktree merge FE?BE for paired verify ? **not pushed**, not merged to master | see Checks |


## CI green evidence (2026-09-10 UTC)

| PR | Branch tip | Actions run | Result |
|----|------------|-------------|--------|
| #4 | `d76da28d8476fcb1976c6c7d55e22d81a6f03627` | [34431721897](https://github.com/gaganpasupuleti/job-ready-platform/actions/runs/34431721897) | pytest + lint/build + Playwright **success** |
| #5 | `00bab6388b8d6f6847898a2e9d75099fdb0d62c7` | [34431716792](https://github.com/gaganpasupuleti/job-ready-platform/actions/runs/34431716792) | pytest + lint/build + Playwright **success** |
| #3 | Alembic 014 only | ? | Superseded by #4 ancestry; comment recorded; do not double-merge |
| Integ worktree | `sprint1-integ-local-only` @ `f5126f1` (local-only, not pushed) | FE+BE paired checkout | Contains 014+015 + AUTH-01 `queryClient` |

## Phase 2 — Coding + visual + MCQ reliability (in progress)

| Checkpoint | Status | Notes |
|------------|--------|-------|
| Sprint 1 verification | **GREEN** (prior CI) | PR #4/#5 Playwright + pytest + lint |
| Verification gap close-out (2026-09-10) | **landed** | BE `c6a1666` / `db55bab`; FE `eb9f871` / `87f7018` |
| Local stack restore re-verify (2026-09-11) | **GREEN** | Health ok; Redis PONG; Vite 200; keep stack running |
| Python Playground (distinct from assessed) | **landed FE** | `/practice/python` + `/practice/playground` |
| Playground API | **landed BE** (learning-runtime) | `POST /api/v1/coding/playground/run` honest unavailable |
| Visual foundation (compact shells/tokens) | **verified FE** | Source Sans 3; `Field` controls; shells; densified screens + screenshot review fixes |
| Assessed coding workspace polish | **verified FE (UI)** / **blocked (grading)** | Sticky Run/Submit; drafts; Judge0 off → Run/Submit 503, no fake grades |
| MCQ exam reliability | **implemented + tested** | Finalize autosaves on complete; stale-session expire fix; flush/sequence; inline confirm; unique answered counts |
| Screenshots + keyboard | **captured + reviewed** | UI fixes: answered % label, disabled button contrast, DSA toolbar wrap |
| E2E | coding + mcq + visual | See Checks / Evidence reconcile |

## Evidence reconcile (2026-09-11)

### 10/10 visual+coding+mcq run (pre-reliability product tip)

| Field | Value |
|-------|-------|
| What ran | `coding.spec` + `mcq.spec` + `visual-foundation.spec` + `visual-foundation-shots` (desktop project) |
| Result | **10/10 passed** |
| FE product commit exercised | `9f22d19` (compact UI + MCQ resume polish) |
| FE tip then (ledger pins) | `6131cbd` local **ahead of** `origin/...` @ `21a811d` — **not** on remote PR head |
| BE runtime tip | `3870032` (last BE **runtime** commit). Later BE commits `747aa82`/`de57fdd`/`…` are **docs-only** ledger mirrors |
| Integ worktree | `4513da6` + live file sync of FE `9f22d19` tree (local-only) |
| Manifest | regenerated `backend/e2e-manifest.json` (local, gitignored); coding `f2e249de-…` / `echo-input`; SHA256 prefix `91D6C81BD5996BAE` |

### Reuse mapping

| Prior result | Reuse? | Why |
|--------------|--------|-----|
| Auth+playground **11/11** @ FE `21a811d` + BE `3870032` | **Yes** for auth/playground until those files change | Reliability/visual edits did not touch AUTH-01 or playground run path |
| pytest sprint1 **12 passed** @ BE `3870032` | **Partial** | Still valid for auth/mistakes/readiness; **new** `test_practice_exam_reliability.py` must be counted separately |
| smoke/hub **12 passed / 2 coding skipped** (no manifest) | Superseded | Manifest regenerated; coding specs then executed |
| Visual 10/10 @ product `9f22d19` | Baseline for UI | Follow-up reliability FE/BE commits add runtime MCQ fixes — re-ran coding+mcq **6/6** after those |

### Local tip vs remote PR head (do not conflate)

| Stream | Local tip (unpushed) | Remote tracking tip | Notes |
|--------|----------------------|---------------------|-------|
| FE `feature/jobready-frontend-experience-v4` | ahead (includes `9f22d19` + later) | `21a811d` | Unpushed work is **not** in GitHub PR #5 until pushed |
| BE `feature/jobready-learning-runtime-v4` | ahead (docs + MCQ reliability) | `3870032` | Docs-only commits first; then runtime MCQ service/tests |

## MCQ reliability acceptance matrix

| Gate | Status | Evidence |
|------|--------|----------|
| Multi-select save/restore | **verified** (BE) | `test_exam_multi_select_autosave_restore` |
| Rapid changes / stale responses | **implemented** (FE seq) / **partial** | FE `saveSeqRef` ignores stale autosave UI updates; DB unique constraint still deferred |
| Pending saves on nav/Finish | **implemented** | `flushAutosave` before Next/navigator/complete; timed settle |
| Refresh/resume w/o resetting deadline | **verified** | BE preserves `expires_at` on get; e2e Resume test |
| Server expiry + reject late writes | **verified** | `test_exam_expiry_rejects_late_writes…` + in-memory session refresh after expire |
| Idempotent finalize + authoritative results | **verified** | complete grades autosaves; double complete OK |
| No answer leakage in active exam | **verified** | options omit `is_correct`; exam answer `feedback is None`; results gated |

## Coding integration (Judge0)

| Check | Result |
|-------|--------|
| `execution-status.available` | `false` (`enabled=false`, `provider=none`) |
| `POST .../run` / `.../submit` | **503** (`language_id`+`source_code`; re-checked 2026-09-12) |
| Hidden tests in problem detail | **not leaked** (`test_cases` absent; `sample_test_cases` only — echo-input) |
| Live correct/WA/CE/RE/TLE | **not run** — no authorized provider reachable |
| Playwright coding specs | UI unavailable banner + **draft persistence** (not live grading) |
| Blocker | **Live grading explicitly blocked** — see Judge0 local gate below |

### Judge0 local gate (2026-09-12) — why no real provider

| Fact | Detail |
|------|--------|
| App config | `JUDGE0_ENABLED=false` in root + `backend/.env` (integ + BE tip). Defaults would probe `http://localhost:2358` only if enabled. |
| Authorized providers | **Self-hosted Judge0 CE only** (`Judge0CodeExecutionService`). No RapidAPI/SaaS client in repo. |
| Local listener `:2358` | None |
| Docker | Not installed (`docker` missing from PATH) |
| WSL2 | Hyper-V / Virtual Machine Platform missing (`HCS_E_HYPERV_NOT_INSTALLED`) — cannot host privileged Judge0 workers |
| Mock executor | **Must not** be treated as live grading evidence |

**Concrete setup to unblock (pick one):**

1. **Remote VPS (documented path):** Follow `docs/JUDGE0_DEPLOYMENT.md` — Ubuntu 22.04 + privileged Docker + Judge0 CE **v1.13.1** (`infra/judge0/docker-compose.yml`), TLS reverse proxy, set Railway/local `JUDGE0_ENABLED=true`, `JUDGE0_URL`, `JUDGE0_AUTH_TOKEN`. Verify with `docs/JUDGE0_VERIFICATION.md` / `pytest tests/test_judge0_live.py` (`JUDGE0_LIVE_TESTS=1`).
2. **Local Linux Docker host:** Enable Hyper-V + install Docker Desktop/WSL2 **or** use a remote Linux box; `cp infra/judge0/.env.example infra/judge0/.env` (fill `JUDGE0_POSTGRES_PASSWORD`, `JUDGE0_REDIS_PASSWORD`, `JUDGE0_AUTH_TOKEN`); `docker compose up -d` from `infra/judge0`; point app `JUDGE0_URL=http://localhost:2358` + matching token; flip `JUDGE0_ENABLED=true`.

Until (1) or (2) is live: keep `JUDGE0_ENABLED=false`; Run/Submit stay **503**; do not enable mocks for acceptance.

## Fresh MCQ validation on tip pair (2026-09-12) — not historical reuse

| Gate | Result | Evidence @ FE `e58b89d`+delta / BE `4efa280` on integ stack |
|------|--------|--------------------------------------------------------------|
| Stack provenance | **confirmed** | API cwd `jobready-sprint1-int/backend` (PID reload worker); Vite cwd `…/frontend`; tip file SHA256 MATCH for practice reliability + session UI; Vite serves `flushAutosave`/`saveSeqRef`; `JUDGE0_ENABLED=false` |
| Immediate submit while autosave pending | **verified** | Live API finalize+idempotent complete; Playwright confirm→results |
| Refresh/resume + multi-select | **verified** | Live API 2-option restore; Playwright refresh `aria-pressed`; resume e2e |
| Expiry + late write | **verified** | Live API late autosave **400** after forced expiry; pytest |
| Repeated final submission | **verified** | Live double `complete`; ownership (other user **404**) |
| Playwright `e2e/mcq.spec.ts` | **6/6** then **2/2 rerun** | See ledger note on FE tip inclusion |
| pytest `test_practice_exam_reliability.py` | **3/3 passed** (fresh) | integ backend = BE tip hashes |

**6/6 inclusion note:** The 2026-09-12 6/6 run already included `aria-pressed` on `QuestionOption` and the new confirm-submit + multi-select tests (synced into integ before that run). After review, asserts were strengthened to require **Practice Complete**, **Score N / M**, **Accuracy**, and unselected `aria-pressed=false`; those two tests were **rerun 2/2 passed** (2026-09-12) against the same PIDs — not a full 6/6 redo.

### Port bind note (not an outage)

Duplicate uvicorn start failed with WinError **10048** (address already in use). Existing healthy listener on `:8000` continued serving. Treat as **duplicate-start**, not application downtime.

### Judge0

Live coding execution/grading remains **blocked** (`enabled=false`, `available=false`, provider `none`). Unavailable/503 checks are **not** grading success evidence.

## V3 design reconcile (repo tips only; standalone preview excluded)

Reference: commits `790e76f`→`28e1212` (product experience v3); inspect tip `feature/jobready-ui-skeleton-premium` @ `c217e4e`. Lineage is **not** ancestral to `e58b89d` (parallel live-API v4). Folders like `codequest-ui-lab` / `jobready-ui` are **not** repository implementation.

| Route / surface | Status vs V3/premium |
|-----------------|----------------------|
| `/practice/sessions/*`, results, coding/DSA/SQL catalogs+workspaces, python playground | **aligned** (VF compact / polish only) |
| `/`, `/login`, `/practice` hub, `/learn` list+detail, `/jobs` hub, `/readiness*` | **needs structural redesign** |
| `/assessments*`, `/mock-interviews*`, `/resume-lab`, `/progress`, `/certificates*`, `/activity`, `/profile`, `/settings`, `/notes`, `/learning-paths*`, `/live-classes` | **missing from app** (or PlaceholderPage) |
| `/admin/*` | **admin-only defer** |

## Verification gap close-out (this checkpoint)

| Gap | Result | Evidence |
|-----|--------|----------|
| Playground heading | Fixed | Header title is `<p>`; page keeps single main `h1`; e2e uses `getByRole('main').getByRole('heading', { level: 1 })` |
| AUTH-01 | Strengthened | Real `/applications` note via API; SPA switch; delayed A success + A 401 after B; no sessionStorage-only markers; logout requires visible Logout |
| Stale 401 after switch | Fixed | `api/client.ts` ignores 401 when request Authorization does not match current token |
| Lesson verification | Replaced | `test_lesson_attempt_verification_via_service` hits `/lessons/{id}/attempt` + completion gate |
| Mistake concurrency | Extended | Same-event replay retained; distinct-event barrier race + item-create IntegrityError recovery |

## Explicitly deferred

- Full Master Plan Phase 2–5 remainder (GSAP motion system, whole-product restyle beyond practice shells)
- Retry Incorrect MCQ session API
- Validated-jobs / PR #1 content expansion
- Production Railway deploy / Judge0 enablement
- Broad `learn_service.py` rewrite (only scoped `is_correct` trust fix in Sprint 1)

## Inventory (baseline)

| Area | Path | Notes |
|------|------|-------|
| Routes | `frontend/src/routes/index.tsx` | Deep links for SQL/DSA/AI/infra preserved |
| Tokens | `frontend/src/index.css` | Light density only in Sprint 1 |
| Nav | `frontend/src/components/navigation/navConfig.ts`, `Sidebar.tsx` | Primary Today set; deep links under Practice tracks / More |
| Auth cache | `frontend/src/hooks/useAuth.tsx`, `queryClient.ts`, `api/client.ts` | AUTH-01 clear on auth transitions + 401 + cross-tab |
| SQL/DSA workbench | PR #2 on master | Not regressed |

## Checks

| Check | Result | When / revision |
|-------|--------|-----------------|
| Local stack | **up** (kept running) | Postgres `:5432`; Redis `:6379`; uvicorn `:8000`; Vite `:5173` |
| Health | `database/redis/sql_sandbox=ok`, `judge0=disabled` | re-checked during reliability work |
| Auth+playground Playwright | **11/11** (reuse) | FE `21a811d` + BE `3870032` |
| Visual 10/10 Playwright | **passed** | FE product `9f22d19` + manifest `echo-input` / `91D6C81BD5996BAE` |
| Coding+MCQ Playwright (historical post-reliability) | **6/6** | prior integ; coding unavailable+draft |
| MCQ Playwright **fresh** @ tips | **6/6** | 2026-09-12; reused Vite :5173 (`E2E_SKIP_WEBSERVER=1`); FE tip + `QuestionOption` aria-pressed |
| `pytest` exam reliability **fresh** | **3/3** | 2026-09-12; BE `4efa280` hashes; live API gates also OK |
| Coding API grading | **blocked** | Judge0 disabled — **not** counted as grading success |
| Uvicorn bind 10048 | **duplicate-start** | Existing :8000 stayed healthy; failed second start only |
| FE local tip | `e58b89d` | ahead of remote `21a811d` (**unpushed**) |
| BE local tip | `4efa280` | ahead of remote `3870032` (**unpushed**) |

## Uvicorn exit root cause (prior session)

Fatal bind error was **not** Redis. Evidence from failed start attempt: `Application startup complete` then `ERROR: [Errno 10048] ... bind on address ('127.0.0.1', 8000)` (port already held by a hung python). Redis `ConnectionError` lines were non-fatal warnings in lifespan. Later healthy process was killed while hung (`Stop-Process`), producing clean exit.

## Blockers

1. **PR #3** (Alembic 014) — OPEN. Prefer close/skip once PR #4 lands; do not double-merge 014.
2. Docker Desktop / WSL2 Hyper-V missing — cannot use documented `infra/docker-compose.yml` until installed; local workaround uses native Postgres + portable Redis.
3. Gk gate before any master merge / Railway redeploy.
4. **Judge0 live grading** — blocked until self-hosted CE is reachable (Docker/WSL2 or VPS). `JUDGE0_ENABLED` stays false; mocks are not acceptance evidence.

## File change log (filled as work lands)

### Backend (`feature/jobready-learning-runtime-v4`)

- `docs/FRONTEND_REDESIGN_STATUS.md`, `docs/FRONTEND_BACKEND_DEPENDENCIES.md` ? Phase 0 ledgers
- `backend/app/core/config.py` ? login throttle + admin bootstrap settings
- `backend/app/services/auth_throttle.py` ? Redis/process-local login failure budget
- `backend/app/services/auth_service.py` ? throttle on login
- `backend/app/seed/runner.py` ? `ensure_seed_admin`; no default prod credentials
- `backend/app/services/mistake_service.py` ? event-idempotent upsert; live helpers; retry href fixes
- `backend/alembic/versions/015_mistake_source_events.py` ? DB unique event identity for concurrency
- `backend/app/services/sql_practice_service.py` / `coding_service.py` ? live wrong-submit mistakes
- `backend/app/readiness/skill_mapping.py` ? remove unsafe aliases
- `backend/app/readiness/formulas.py` + `readiness_service.py` + `schemas/readiness.py` ? denominator + formula version
- `backend/app/services/learn_service.py` ? stop trusting client `is_correct` for verified achievement
- `backend/tests/test_auth_hardening.py`, `test_sprint1_reliability.py`
- MCQ exam reliability (2026-09-11): `practice_service` finalize autosaves on complete; refresh session after expire; navigator/answered counts treat selections as responses; `test_practice_exam_reliability.py`; `get_answer` latest-row limit

### Frontend (`feature/jobready-frontend-experience-v4`)

- `frontend/src/queryClient.ts` — shared QueryClient + `clearAuthQueryCache`
- `frontend/src/App.tsx`, `hooks/useAuth.tsx` — clear cache on login/logout/register; cross-tab; failed logout
- `frontend/src/api/client.ts` — 401 clears token + query cache
- `frontend/src/components/navigation/navConfig.ts` — primary Today set + demoted deep links
- Dashboard / Mistakes / Readiness / Jobs private queryKeys scoped with `user.id`
- `frontend/src/pages/readiness/ReadinessPage.tsx` — withhold misleading overall %; formula honesty
- `frontend/src/pages/practice/PracticePathPage.tsx` — always show `N% progress` (+ test id)
- `frontend/e2e/auth.spec.ts` — AUTH-01, failed logout, stale 401, cross-tab
- `frontend/e2e/hub.spec.ts`, `smoke.spec.ts`, `helpers.ts` — Playwright stability
- Visual foundation (2026-09-11): `Field.tsx`, compact `index.css` shells, Practice Hub/Coding/MCQ catalog/session/results, DSA sticky assessed chrome, Python playground density
- MCQ Resume via `PracticeHistory` for `active` sessions; `e2e/mcq.spec.ts` resume coverage
- MCQ reliability FE: autosave sequencing/flush, answered-% chrome, inline Confirm submit, timer arming, completed→results redirect
- `QuestionOption` `aria-pressed` for selected state; `e2e/mcq.spec.ts` confirm-submit→results + multi-select refresh restore
- `e2e/visual-foundation.spec.ts`, `e2e/visual-foundation-shots.spec.ts`, artifacts under `e2e/artifacts/visual-foundation/`
- Ledgers mirrored across streams for PR reviewability
- 2026-09-12: stack provenance confirmed (integ cwd + tip SHA MATCH); bind 10048 documented as duplicate-start
