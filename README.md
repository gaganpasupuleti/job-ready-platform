# Job Ready Platform

MVP job-preparation platform: practice (MCQ, coding, SQL), learn/projects, AI prompt drills, cloud/DevOps/cyber scenarios, interviews, jobs/applications, and readiness / mistake book.

## Stack

| Layer | Tech |
|-------|------|
| Frontend | React 19, Vite, TypeScript, Tailwind, React Router, TanStack Query |
| Backend | FastAPI, SQLAlchemy 2, Alembic, Pydantic |
| Data | PostgreSQL (app), PostgreSQL (SQL sandbox), Redis (optional) |
| CI | GitHub Actions — pytest, lint, build, Playwright, SQL sandbox |
| Deploy | Railway (frontend, backend, app Postgres, sandbox Postgres, Redis) |

## Modules (MVP)

- **Practice** — aptitude/MCQ, DSA/coding, SQL sandbox
- **Learn / Projects** — paths, courses, project workspaces
- **AI** — prompt challenges (deterministic, no LLM)
- **Infrastructure** — cloud / DevOps / cybersecurity scenarios
- **Interviews** — packs, self-review, company prep
- **Jobs** — browse, save, applications, requirement coverage
- **Readiness** — role readiness, mistakes, recommendations

## Local setup

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env

# Postgres + Redis (+ SQL sandbox Postgres on :5433)
docker compose -f infra/docker-compose.yml up -d postgres redis postgres_sql_sandbox

cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
python -m app.seed.runner
python -m app.readiness.backfill

uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

```bash
cd frontend
npm ci
npm run dev
```

- App: http://127.0.0.1:5173  
- API docs: http://127.0.0.1:8000/docs  
- Health: http://127.0.0.1:8000/api/v1/health  

Dev admin (local/seed only): `admin@jobready.dev` — never use default passwords in production.

## Migrations & seed

```bash
alembic upgrade head          # 001 … 013_build10
python -m app.seed.runner     # idempotent content seed
python -m app.readiness.backfill
```

Fresh-DB gate (destructive to local schema): `python scripts/fresh_db_gate.py` from `backend/`.

E2E users/content: `E2E_ALLOW_SEED=1 python -m app.seed.e2e` (never auto-run in production).

## Tests

```bash
# Backend
cd backend && pytest -q

# Frontend
cd frontend && npm run lint && npm run build
npx playwright test --project=desktop
```

## Deployment

See [docs/RAILWAY.md](docs/RAILWAY.md), [docs/BACKUP_RESTORE.md](docs/BACKUP_RESTORE.md), [docs/RELEASE_NOTES_MVP.md](docs/RELEASE_NOTES_MVP.md).

Production must set:

- `APP_ENV=production`
- `DATABASE_URL`, strong `JWT_SECRET_KEY`
- `CORS_ORIGINS` = frontend origin only
- `VITE_API_BASE_URL`, `VITE_ENABLE_DEV_LOGIN=false`
- SQL sandbox URLs when `SQL_EXECUTION_ENABLED=true`
- `JUDGE0_ENABLED=false` until a dedicated Judge0 host exists

Smoke: `python scripts/smoke.py --base-url https://<api-host>`

## Architecture (summary)

```
Browser → FastAPI modular monolith
        → App Postgres
        → Redis (optional)
        → SQL sandbox Postgres (student SELECT only)
        → Judge0 (optional / currently disabled)
```

## Important MVP limits

- **Judge0 disabled** — coding execution unavailable
- **No external LLM**
- **No hiring probability** claims — readiness / requirement coverage only

Details: [docs/KNOWN_ISSUES.md](docs/KNOWN_ISSUES.md)

## Docs

| Doc | Topic |
|-----|--------|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design |
| [docs/PRODUCT_MODULES.md](docs/PRODUCT_MODULES.md) | Module status |
| [docs/SQL_PRACTICE.md](docs/SQL_PRACTICE.md) | SQL sandbox |
| [docs/READINESS.md](docs/READINESS.md) | Readiness |
| [docs/RELEASE_NOTES_MVP.md](docs/RELEASE_NOTES_MVP.md) | MVP notes |
| [CHANGELOG.md](CHANGELOG.md) | Version history |
