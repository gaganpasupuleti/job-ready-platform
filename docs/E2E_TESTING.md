# E2E Testing (Build 7.2)

Browser end-to-end tests use **Playwright** against a local frontend + backend + Postgres + Redis + SQL sandbox.

## Prerequisites

- Node 20+
- Python 3.13+ with `backend/requirements.txt` installed
- Docker Compose services from `infra/docker-compose.yml` (app Postgres, SQL sandbox on `5433`, Redis)
- `JUDGE0_ENABLED=false` (coding Run/Submit stay disabled; E2E asserts that)

## Environment

| Variable | Default | Purpose |
| --- | --- | --- |
| `E2E_BASE_URL` | `http://localhost:5173` | Frontend origin |
| `E2E_API_URL` | `http://localhost:8000` | API origin (for docs/scripts) |
| `E2E_ALLOW_SEED` | unset | Must be `1` outside development/test to run E2E seed |
| `E2E_MANIFEST_PATH` | optional | Where seed writes fixture JSON |
| `E2E_SKIP_WEBSERVER` | unset | Set to skip Playwright starting Vite (when you already run `npm run dev`) |
| `VITE_API_BASE_URL` | `http://localhost:8000` | Frontend API base |
| `VITE_ENABLE_DEV_LOGIN` | `false` recommended for E2E | Avoid pre-filled admin credentials during tests |

## Seed deterministic fixtures

From `backend/`:

```bash
set E2E_ALLOW_SEED=1
python -m app.seed.e2e ../frontend/e2e/fixtures/manifest.json
```

Creates/updates:

- Student: `e2e.student@jobready.dev` / `E2eStudent123!`
- Admin: `admin@jobready.dev` / `Admin123!` (from base seed)
- Stable SQL slug `active-catalog-items` and known accepted query
- Existing paths/projects/courses/prompts/scenarios from idempotent seeds
- Build 8 interview packs/questions (`seed_build8_content`) when available

**Safety:** seed refuses production unless `E2E_ALLOW_SEED=1`.

Interview Playwright specs: `frontend/e2e/interview.spec.ts` (hub, study, mock reveal, company prep, admin block).

## Run stack

Terminal 1 — backend:

```bash
cd backend
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Terminal 2 — frontend:

```bash
cd frontend
npm run dev
```

## Run Playwright

```bash
cd frontend
npx playwright install chromium
npm run test:e2e
```

Useful variants:

```bash
npx playwright test e2e/auth.spec.ts
npx playwright test --project=desktop
npx playwright test --project=mobile
npm run test:e2e:ui
npm run test:e2e:report
```

## Reports

On failure Playwright retains:

- screenshots
- traces
- video

HTML report: `frontend/playwright-report/`

## Known limitations

- **Judge0 is off in E2E app servers (`JUDGE0_ENABLED=false`).** Coding E2E verifies the unavailable banner and disabled Run/Submit. Do not fake execution results. Backend unit tests may set `JUDGE0_ENABLED=true` so mocked Judge0 paths still run.
- **SQL E2E skips** when `GET /api/v1/sql/execution-status` reports `sandbox_unavailable` or `available=false`. Start `postgres_sql_sandbox` (Docker Compose) before expecting SQL Run/Submit coverage.
- **Retry Incorrect (MCQ)** is deferred: creating a session from only incorrect question IDs needs a clean API extension; documented for a later build.
- Some flows skip gracefully when optional fixtures (prompt/scenario checklists) are missing from the UI.
- Do **not** hardcode Railway production URLs in tests.
- **Vitest** was not added in Build 7.2 to avoid churn; Playwright is the primary browser QA layer.

## Branch protection recommendation

When CI is green on `master`, require:

1. Backend pytest
2. Frontend lint + build
3. Playwright E2E (desktop project)

before merge. Do not enable GitHub branch protection without an explicit owner decision.
