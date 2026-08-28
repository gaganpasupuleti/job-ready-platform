# Development Guide

## Environment Setup

1. Copy environment files:
   ```bash
   cp .env.example .env
   cp frontend/.env.example frontend/.env
   ```

2. Start infrastructure:
   ```bash
   docker compose -f infra/docker-compose.yml up -d postgres redis
   ```

3. Backend virtual environment:
   ```bash
   cd backend
   python -m venv .venv
   .venv\Scripts\activate        # Windows
   source .venv/bin/activate       # macOS/Linux
   pip install -r requirements.txt
   ```

4. Frontend dependencies:
   ```bash
   cd frontend
   npm install
   ```

## Database Migrations (Build 2+)

```bash
cd backend
alembic upgrade head
```

If PostgreSQL user/database do not exist yet:

```bash
cd backend
python scripts/setup_db.py
alembic upgrade head
python -m app.seed
```

## Seed Data (Build 2)

```bash
cd backend
python -m app.seed
```

**Development admin credentials:**

| Field | Value |
|-------|-------|
| Email | `admin@jobready.dev` |
| Password | `Admin123!` |

Seed includes taxonomy across Placement, Technical, AI, Cloud, DevOps, and Cybersecurity domains plus **37 sample development questions** marked `is_sample=true`. These are for engine testing only — not production content.

## Running Locally

### Backend

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm run dev
```

## Database Migrations

When domain models are added:

```bash
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## Code Quality

### Backend

```bash
cd backend
ruff check .
pytest
```

### Frontend

```bash
cd frontend
npm run build
npm run lint
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://...` | PostgreSQL connection |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |
| `JUDGE0_URL` | `http://localhost:2358` | Future code execution service |
| `JUDGE0_API_KEY` | empty | Future Judge0 API key |
| `VITE_API_BASE_URL` | `http://localhost:8000` | Frontend API base URL |

## Adding a New Module

1. Add route config in `frontend/src/routes/moduleRoutes.tsx`
2. Add nav item in `frontend/src/components/navigation/navConfig.ts`
3. Add module entry in `backend/app/services/modules_service.py`
4. Create domain model in `backend/app/models/<domain>.py` when data is needed
5. Add service, repository, and router as the module gains real functionality

## Build 1 Boundaries

Build 1 delivered the shell only. Build 2 adds authentication, universal question bank, and MCQ practice.

Still deferred:

- DSA / Judge0 / Monaco
- Full assessments and contests backend
- AI interviews and prompt evaluation
- Jobs backend
- Readiness scoring backend
- Payments and notifications
