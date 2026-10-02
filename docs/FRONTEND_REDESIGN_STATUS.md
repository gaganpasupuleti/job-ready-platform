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

## V4 design-reference integration (2026-09-12)

| Field | Value |
|-------|-------|
| Reference | `backend/design-reference/jobready-v4` (README + INTEGRATION_NOTES) |
| FE tip after shell | 4edecee (4edeceee286f46521812bf0ecd679b1f04cb306a); modules land 3cd1665 |
| Shell | Horizontal **masthead** + JR monogram `jobready.` + primary nav + More drawer |
| Tokens | Stone canvas `#E8EAE7` / surface `#F4F5F1` / steel accent `#40596B` |
| Overview | Live continue/readiness — preserved |
| Practice hub / Learn | V4 queue rows, track selectors, curriculum layout — **live APIs** |
| Studios | `studio-main` / `studio-topline` / `editor-toolbar` on DSA/SQL/Python — Monaco/drafts/Run-Submit preserved; Judge0 unavailable honest |
| Jobs | Live hub tabs + filter bar; Mark applied when preparing/saved/none; post-apply View application |
| Judge0 | Still **blocked** (separate infra); coding e2e = unavailable + drafts only |
| package.json / lockfile | **unchanged** |

### Browser checks (reused API PID 20912 / Vite PID 25088)

| Suite | Kind | Result | Notes |
|-------|------|--------|-------|
| lint / build | functional | **passed** | FE tip |
| desktop hub+mcq+coding+jobs+shots | functional + visual | **15 passed / 2 skipped** | jobs mark-applied fixed; shots under `e2e/artifacts/v4-modules/` |
| mark applied desktop+mobile | functional | **2/2** | dynamic clean listing; persist + refresh asserts |
| mobile hub+jobs+shots (excl. dirty apply flake) | mixed | hub/shots OK; apply fixed on rerun | |
| Judge0 live grading | — | **not run** | provider unreachable |

**Functional vs visual:** Jobs apply/persist, hub search, MCQ, coding unavailable+drafts = functional. `v4-modules-shots` PNGs = visual comparison artifacts vs reference (manual review).

Skipped / not claimed: enabling Judge0; importing preview `jobs-data.js`; BE ledger commits.

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

## Responsive v5 (2026-09-14) — frontend only

| Field | Value |
|-------|-------|
| Branch | `feature/jobready-frontend-responsive-v5` |
| Base | `origin/master` @ `ab55fce` |
| Worktree | `../jobready-fe-responsive` |
| Scope | Colors, pill size, spacing, content-rail alignment, breakpoints, practice track nav |
| Preserved | Segoe UI / Cascadia Code stack, JR monogram, auth cache, jobs family filters, SQL workbench, MCQ session/autosave, Python execution locks |
| Backend | **unchanged** — missing contracts recorded in `docs/FRONTEND_BACKEND_DEPENDENCIES.md` |
| Merge / deploy | **not done** |

## Phase 4 slice (2026-09-28) — frontend only, mock preview

Branch `feature/jobready-frontend-redesign`. These rows are not production verification. A mock that says Java or SQL can run does not prove the real runtime.

| Check | Result |
|-------|--------|
| Compact coding and SQL catalogs, runtime notice before open | Mock preview and `e2e/phase4-mock.spec.ts` |
| Loading, failed, and unavailable capability copy | Mock Playwright only |
| Coding pane switch keeps the selected language | Mock Playwright only |
| SQL Problem / Schema / Editor / Output keeps the draft | Mock Playwright only |
| Playground has no Submit shortcut; Python has no Run or Submit | Mock Playwright only |
| Lesson Next stays closed when the next block is locked; reading lessons omit empty Hints/Solution | Mock Playwright and unit checks |
| Real coding or SQL run and submit | **Pending.** Local API was not used. Judge0 and Python execution stay off. |
| `feature/student-library` | Not modified and not integrated |

## Assessment, review, and progress slice — not a Phase 4 close-out

Parent `75ee7b61f7da4ae218ceeba94dbabfd18d54839e`. This section ships in the same local commit. It does not mark Phase 4 complete. Fixture results are not real-API verification. Judge0 stays off. No production submissions were created.

| Item | Status |
|------|--------|
| Technical MCQ and aptitude names, subject grouping, compact setup | Done in the UI |
| History scoped to the subjects on the page | Done. Mock Playwright |
| Honest catalog loading, empty, and failed states | Done. A missing subject is not reported as an API outage |
| Answer restore, multi-select, resume, expiry, keyboard focus | Mock Playwright only (`e2e/phase4-assessment-mock.spec.ts`) |
| Duplicate submit and reconnect | **Partial.** Existing confirm-submit remains. Not retested against a real API |
| Review topic labels, compact totals, no new retry session | Done. Global weak topics stay labeled as all-subject |
| Self-check versus lesson completion versus graded results | Done in copy and path/lesson labels. Backend rules unchanged |
| Unknown or failed progress shown as zero | Guarded on the path page, overview, and review totals |
| Real assessment run, submit, and persisted progress | **Pending** |

### Mock preview

The fixture server is `frontend/scripts/dev-mock.mjs`. It is opt-in and is not imported by the app. Default port is **8099**, not the normal backend port. The committed Vite proxy still defaults to `http://127.0.0.1:8000`.

Start the fixture API, from `frontend`:

```
npm run dev:mock
```

Start the preview against that fixture, in another shell, from `frontend`:

```
$env:DEV_API_PROXY='http://127.0.0.1:8099'
npm run dev -- --host 127.0.0.1 --port 5193
```

Stop each process on its own. Do not stop whatever is listening on port 8000 unless its command line is this fixture script.

### Screenshots

Before: `before-mcq`, `before-aptitude`, `before-mistakes`, `before-overview` at desktop and 390px.

After: `after-mcq`, `after-aptitude`, `after-mistakes`, `after-path` at desktop and 390px.

Files are under `C:\Users\Admin\AppData\Local\Temp\cursor\screenshots`. Page overflow was 0. These shots use the fixture API.

### Next

Phase 5 module coverage is recorded below. Real-API coding, SQL, and assessment checks from Phase 4 stay pending.

## Phase 5 — remaining student modules (not a redesign close-out)

Parent `218f1d334f2c683a043c9900cdfddc05b9c0c5c4`. Local commits `8bbc7b0` (materials, assignments, projects) and `0411570` (typing, readiness, interviews, tracks, bookmarks, More). Frontend only. Backend, migrations, service configuration, Judge0, and `feature/student-library` were not changed. Nothing was pushed, merged, or deployed. Mock checks are not production verification.

| Module | Status |
|--------|--------|
| Materials | Done in the UI. Type and level labels are readable. Unread items no longer repeat “Not marked read”. Empty filter lists are hidden. Read state, download, and the self-reported note stay. |
| Assignments | Done in the UI. A family filter appears only when there is more than one family. Locked, draft, and not-started stay distinct. Instructions stay in the reading column. Rubric, answer text, evidence URL, draft, and manual submit stay. |
| Projects | Done in the UI. Available projects are listed first. Coming-soon items are not links and are not also labeled available. Category chips wrap. No generic submission form was added. |
| Typing | Partial visual alignment only. Shared text, surface, and accent tokens replace the private green palette. Layout, fullscreen, passages, scoring, and timing were not changed. |
| Readiness | Done in the UI for the existing payload. Unconfigured users get “Set a target role” to job preferences. The page does not calculate a new score. Evidence copy replaces the formula prompt. |
| Interviews | Done in the UI. A hub with no reviewed questions says so, instead of a 0% bar. An empty session does not pretend it has a question number. |
| AI, Cloud, DevOps, Cybersecurity | Done in the UI. Track cards describe the topic. Continue is used only for a saved lesson, problem, project, or challenge. Shared catalog destinations are labeled as shared. |
| Prompt challenges and scenarios | Done in the UI. One heading, readable links, no invented best score, wider scenario text, and larger answer targets. |
| Bookmarks | Done in the UI. Empty MCQ and prompt lists link to a real catalog. Counts are omitted while loading. |
| More and account | Done for the existing menu. Opening More focuses the first destination. Escape returns focus to More. No Profile or Settings page was added. |
| Library, Support, Notifications | Blocked. They are not on this base. They stay on `feature/student-library` and were not removed or integrated. |

### Checks

| Check | Result |
|-------|--------|
| `npm run test:unit` | 20 passed |
| `npx playwright test e2e/phase5-mock.spec.ts --project=desktop` | 8 passed. Every `/api` call is fulfilled in the spec. Unmatched API calls return 599. |
| `npx tsc -b` and `npm run build` | Passed. The existing large-chunk warning remains. |
| `npm run lint` | Exit 0. Pre-existing `set-state-in-effect` warnings were not introduced by this slice and were not rewritten. |
| Desktop 1440 and 390 | After shots for materials, assignments, projects, typing, readiness, interviews, AI, prompt challenges, and bookmarks. Page overflow 0. |
| 768 | Projects, typing, and bookmarks. Page overflow 0. |
| Keyboard | Mock test: More opens with focus on the first link; Escape returns focus to More. |
| Real studio, project, readiness, interview, AI, and scenario APIs | **Pending.** |
| Real coding, SQL, and assessment run/submit from Phase 4 | **Pending.** |

### Screenshots

Fixture-backed, not production. Paths are under `docs/evidence/phase5/`.

Before: `before/materials-1440.png`, `before/assignments-1440.png`, `before/projects-1440.png`, `before/typing-1440.png`, `before/readiness-1440.png`, `before/interviews-1440.png`, `before/ai-1440.png`, `before/prompts-1440.png`, `before/bookmarks-1440.png`, plus the same names at `390`, `before/projects-768.png`, and `before/more-menu-1440.png`. The before preview did not include studio, project, or AI fixtures, so several before shots are empty or error states.

After: the same route names at `1440` and `390` under `after/`, plus `after/projects-768.png`, `after/typing-768.png`, and `after/bookmarks-768.png`. After shots intercept `/api` in the browser, so they show the new layout with fixture data.

### Preview

The fixture server is still `frontend/scripts/dev-mock.mjs` on port **8099**. It does not yet include studio, project, interview, or AI payloads. Phase 5 browser checks used Playwright route interception instead.

```
npm run dev:mock
```

```
$env:DEV_API_PROXY='http://127.0.0.1:8099'
npm run dev -- --host 127.0.0.1 --port 5193
```

Stop each process on its own. Do not stop port 8000 unless that listener is this fixture.

### Still open

Phase 3 jobs and overview UI is in `83783fa`. Seeded application flows and real job data are not signed off.

Phase 4 real-API checks stay pending: coding and SQL run/submit, assessment submit, duplicate submit, and reconnect. Judge0 and Python execution stay off.

Phase 6 release gates in the implementation plan stay unchecked. This branch is not release-ready.

## Phase 6 verification — not a release

Parent `cce517e`. Frontend fix commit `90921d4`. Frontend only. `feature/student-library` was not modified or integrated. Nothing was pushed, merged, or deployed. Plan section 11 checkboxes stay unchecked.

### Fixes in this slice

- Learn catalog no longer repeats each course in a sidebar and a tile. Level labels are readable. Progress text says lesson progress.
- Application pipeline columns use the same labels as the status badge (`Preparing`, not a raw status).
- Jobs tabs and summary counts stay blank or show an em dash when a count is missing. They do not print `undefined`.
- The masthead can wrap, so a 200% zoom of the desktop nav does not widen the page.
- Bookmark tabs wrap at 360px. `Prompt Challenges` is no longer clipped.

### Route and state coverage

UI means the page exists and uses the shared shell. Mock means a Playwright fixture exercised it. Real API means the local backend below. A mock row is not a real-API row.

| Route | UI | Mock | Real API | Notes |
|-------|----|------|----------|-------|
| `/jobs` Browse | Implemented | Overflow and long-title fixture | Not rechecked this slice | Counts no longer show `undefined` |
| `/jobs/recommended` | Implemented | Overflow | Not rechecked | Unconfigured state links to preferences |
| `/jobs/saved` | Implemented | Empty state in the overflow sweep | Not rechecked | Empty state links to browse |
| `/jobs/applications` and detail | Implemented | One preparing application; readable stage | Not rechecked | Detail notes were not written |
| `/jobs/preferences` | Implemented | Labels for role and locations | **Verified** for a new user | Save 204; a second user did not see that role |
| `/` Overview | Implemented | Overflow sweep | Not rechecked | |
| `/practice` | Implemented | Overflow sweep | Not rechecked | |
| `/learn` catalog | Implemented | Single course link; `Beginner` | Not rechecked | Duplicate sidebar removed |
| `/learn/courses/...` curriculum and lesson | Implemented earlier | Phase 4 lesson mock | Not rechecked | |
| `/learn/syllabus` | Implemented | Overflow sweep, empty or error if the fixture is thin | Not rechecked | |
| `/learn/materials`, assignments | Implemented | Phase 5 and Phase 6 | Not rechecked | |
| `/practice/projects` | Implemented | Phase 5 | Not rechecked | |
| `/practice/mcq`, `/practice/aptitude`, session, results | Implemented | Phase 4 mock | **Partial real API** | Start, answer restore, complete, and results succeeded. See below |
| `/practice/dsa` | Implemented | Phase 4 mock; overflow sweep | **Unavailable verified** | `execution_available` is false. Judge0 stays disabled |
| `/practice/sql` | Implemented | Phase 4 mock; overflow sweep | **Unavailable verified** | SQL sandbox is unavailable. Run and submit were not executed |
| `/practice/playground`, Python | Implemented | Phase 4 mock | Not rechecked | Python stays locked |
| `/practice/typing` | Implemented | Phase 6 overflow. Engine not retested | Not a server feature | Timing and scoring were not changed |
| `/mistakes`, results | Implemented | Phase 4 mock; overflow sweep | Not rechecked | |
| `/readiness` | Implemented | Phase 5 | Not rechecked | |
| `/interviews` and secondary interview routes | Hub implemented | Hub overflow and empty progress | Not rechecked | Packs, session, and review were not re-opened |
| `/ai`, Cloud, DevOps, Cybersecurity, prompts, scenarios | Implemented | Phase 5; home and prompt list in the overflow sweep | Not rechecked | |
| `/bookmarks` | Implemented | Empty action; tabs wrap at 360 | Not rechecked | |
| More and account | Implemented | Focus and Escape in Phase 5 | Logout is partial | No Profile or Settings page |
| Library, Support, Notifications | Absent on this base | — | — | Stay on `feature/student-library`. This blocks full module accounting |

### Checks

| Check | Result |
|-------|--------|
| `npm run test:unit` | 20 passed |
| `npx playwright test e2e/phase6-layout.spec.ts --project=desktop -g "top-level routes"` | 1 passed. Widths 1440, 390, and 360. Page overflow 0 after the bookmark wrap |
| Same file, representative widths, catalog/applications, and 200% zoom | 3 passed in the run before the bookmark wrap. Zoom was rechecked after the masthead wrap |
| `npx tsc -b`, `npm run lint`, `npm run build` | Passed. Lint warnings are the pre-existing `set-state-in-effect` set. Build still warns that the main chunk is over 500 kB |
| `frontend/vite.config.ts` proxy default | Unchanged: `http://127.0.0.1:8000`. `dev-mock.mjs` is still opt-in and not imported by the app |
| Phase 4 and Phase 5 mock specs | Not re-run as a full suite. Their earlier results stand |

### Real API

The process on port 8000 is uvicorn from `New folder (5)/backend`, revision `d09ae43`, database `jobready_db` on localhost. Redis is unavailable. This is not the redesign worktree and it is not production. Writes used newly registered users only (`phase6-a-*`, `phase6-b-*`, `phase6-restore-*` at example.com). No existing job or user was edited. Evidence: `docs/evidence/phase6/real-api-result.json`.

| Check | Result | Blocks a frontend release? |
|-------|--------|----------------------------|
| Judge0 disabled, coding `execution_available` false | Verified | No, for shipping the unavailable state. Yes, for any claim that code execution works |
| SQL sandbox unavailable | Verified. Run and submit were not sent | No, for the unavailable message. Yes, for a claim that SQL execution works |
| MCQ start, answer restore, complete, results | Verified on a disposable user | No |
| Duplicate complete | Both calls returned 200. Rejection was not shown | Yes, for the duplicate-submit release check. The confirm dialog remains |
| Reconnect | Not tested | Yes, for that release check |
| Job preference save and isolation | Verified | No |
| Application persistence | Not rechecked | No, this slice did not change the write contract |
| Logout | Frontend still clears the local token. The server returned 200 and the same token still loaded `/auth/me` | Yes, for server-side session end. No, for the client clearing its own session |
| `feature/student-library` | Not integrated | Yes, for the “all modules accounted for” gate |

### Comparable screenshots

Reconstructed in an isolated worktree at `218f1d3`. The main worktree was not checked out. Same fixtures and a 1440px viewport. These are not the original empty before shots.

- Baseline: `docs/evidence/phase6/baseline-218f1d3/` (`materials`, `assignments`, `projects`, `ai`)
- Current Phase 5 UI: `docs/evidence/phase6/current-cce517e/` for the same four pages

The baseline materials page still shows the raw type. The current AI page says no hosted model is called, and RAG says the catalog is shared. Projects on the baseline still treat coming-soon as a muted link; the current page says the project is not open yet.

### Proposed release and rollback

Do not deploy this branch yet. The unchecked plan gates are still open: student-library merge, duplicate submit, reconnect, SQL and coding execution, and an explicit merge decision.

When a release is later authorized: build `frontend` at the reviewed commit, deploy that artifact through the existing frontend process, smoke-test login and one read-only page, and watch auth and route errors. Do not create a production submission as a smoke test.

Rollback: redeploy the frontend artifact from base `31d9a25` (the revision this branch started from). Do not run a database migration as part of that rollback. This slice did not change the backend.

### Preview

Fixture API, from `frontend`:

```
npm run dev:mock
```

Preview against that fixture:

```
$env:DEV_API_PROXY='http://127.0.0.1:8099'
npm run dev -- --host 127.0.0.1 --port 5193
```

The fixture still does not include studio, project, or AI payloads. Those pages were checked with Playwright route interception.

## Closeout — 2026-10-03

Audited revision `5c7cf41`, then the preferences fix in the following commit. Frontend only. `feature/student-library` was not integrated. Nothing was pushed, merged, or deployed. Plan section 11 stays unchecked.

### Frontend

Fixture preview: `http://127.0.0.1:5193` with `DEV_API_PROXY=http://127.0.0.1:8099`. `GET /api/v1/health` returned `{"ok":true}`. That body is the fixture, not the local API.

| Finding | Evidence | Result |
|---------|----------|--------|
| Job preferences crashed when `roles` was missing | `docs/evidence/phase6/audit-5c7cf41/_jobs_preferences-1440.png` | Fixed. `(data.roles ?? [])`. Recheck showed the form at 1440 and 390 with page overflow 0: `preferences-after-fix-1440.png`, `preferences-after-fix-390.png` |
| SQL problem shows execution unavailable | Fixture payload `execution_available: false`. `sql-unavailable-1440.png` | No code change. The banner says SQL execution is unavailable and Run/Submit stay off |
| Coding problem shows the locked sentence when execution is off | Fixture execution status was overridden to unavailable. `coding-unavailable-1440.png` | The page says code execution is coming soon. The fixture’s own coding status says available; that override is not the live API |
| Jobs, courses, interviews, AI, and bookmarks showed loading or an error while the fixture returned 404 | Audit notes in `audit-5c7cf41/findings.json` | Fixture gap. Interviews settled to “Unable to load interview hub.” No layout overflow on the swept routes |
| Jobs request abort | `jobs-error-1440.png` | Caught during the loading state. Not a crash and not an `undefined` count |

### Real API

Local API `http://127.0.0.1:8000`, backend revision `d09ae43` on `feature/student-library`, database `jobready_db` on localhost. Writes used new `phase6-close-*` and `phase6-ui-*` users at example.com. Evidence: `docs/evidence/phase6/real-api-closeout.json` and `docs/evidence/phase6/browser-auth-closeout.json`.

`GET /api/v1/health` returned degraded: database ok, redis unavailable, sql sandbox unavailable, judge0 disabled.

| Check | Result |
|-------|--------|
| Repeated MCQ complete | Passed. Same score `-0.25`, accuracy `0`, completed time, and one history row. One session and one answer before and after the retry. A second answer on the same question returned 400 |
| Mistake rows | Completion itself wrote none. One backfill of that user created 1 mistake item and 1 source event. A second backfill left both counts at 1 |
| Reconnect | Passed. The saved wrong option was restored on a later GET |
| Uncertain complete | Passed. Discarding the first complete body and calling complete again returned the same result |
| Protected route | Passed in the browser. `/practice` without a token opened login |
| Logout cleanup | Passed on the client. The login page returned and `jrp_access_token` was removed |
| Account switch and late 401 | Passed. After user B signed in, a delayed 401 for user A’s preferences request did not clear B. `/auth/me` stayed user B |
| Preference isolation | Passed. User A saved `ai-agent-engineer` (204). User B’s role stayed null |
| Server token revocation | Failed as a backend gap. Logout returned “Logged out successfully” and the same bearer still loaded `/auth/me`. `AuthService.logout` does not revoke the JWT. Not changed |
| Coding execution | `execution_available` false, provider none, judge0 disabled |
| SQL sandbox | `sandbox_unavailable`. `sql_execution_enabled` is true, but port 5433 is closed and Docker is not installed. Port 5432, the app database, is open. Config and volumes were not changed. Run and submit were not sent |

### Jobs coverage and import

Run from the main workspace backend. Read-only coverage and a dry-run import. `--confirm` was not used. No jobs were published.

| Item | Result |
|------|--------|
| Coverage command | `python -m app.jobs.coverage`. SELECT plus ROLLBACK |
| Target | localhost `jobready_db` |
| Counts | 240 jobs, 197 active, 0 expired, 43 archived or inactive. Saved 39. Applications 101 |
| Mapping | Company 51/197 (25.9%), role 24/197 (12.2%), skill 31/197 (15.7%). Active roles: 173 unmapped, Data Analyst 14, Python Developer 4, and one each for AI Engineer, Data Engineer, DevOps Engineer, GenAI Engineer, SOC Analyst, and SQL Developer |
| Gap counts | No company 146, no role 173, no skill 166, no location 29, no valid apply URL 162, malformed URLs 0 |
| Import command | `python -m app.jobs.import_csv content/phase11_jobs_sample.csv` |
| Input | `backend/content/phase11_jobs_sample.csv`, the only jobs CSV in the tree. Rows are sample demo data |
| Dry run | NEW 12, UPDATE 0, DUPLICATE 0, INVALID 0, then ROLLBACK |
| Student listings | Unchanged. Confirming would insert those 12 rows as ACTIVE, which is the student listing filter, so they would not stay unpublished. There is no second mapping command |

Copies of the coverage and dry-run JSON are in the main workspace at `docs/evidence/jobs-coverage-2026-10-03.json` and `docs/evidence/jobs-import-dry-run-2026-10-03.json`. They are not part of this frontend branch.

### Remaining blockers

| Blocker | Owner | Next action |
|---------|-------|-------------|
| `feature/student-library` is not on this branch | Release owner | Keep it separate until an explicit merge is requested |
| Server logout does not revoke the JWT | Backend | Add revocation only if the product requires a dead token after logout |
| SQL sandbox process is not running on port 5433 | Local infrastructure | Start the documented sandbox without changing production config, then rerun SQL execution |
| Judge0 stays disabled | Release decision | Leave it off until execution is intentionally enabled |
| 173 active jobs have no role mapping, and the sample CSV is unpublished | Jobs content | Supply a reviewed source and mapping rules. Do not confirm the sample file into this database |
| Plan section 11 release gates | Release owner | Leave them unchecked. This branch is not release-ready |
