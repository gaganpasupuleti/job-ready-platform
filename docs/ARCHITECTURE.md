# Architecture

Job Ready Platform is a modular monolith designed for independent domain expansion across practice engines, assessments, jobs, and readiness scoring.

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React + Vite)                   │
│  Shell · Routing · Dashboard · TanStack Query · Axios       │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP /api/v1/*
┌──────────────────────────▼──────────────────────────────────┐
│                   Backend (FastAPI)                           │
│  Routers → Services → Repositories → SQLAlchemy Models        │
└───────┬──────────────────────────────┬────────────────────────┘
        │                              │
┌───────▼────────┐            ┌────────▼────────┐
│  PostgreSQL    │            │     Redis       │
│  Primary data  │            │  Cache / queues │
└────────────────┘            └─────────────────┘

Future (not in Build 1):
┌────────────────┐            ┌─────────────────┐
│    Judge0      │            │  LLM Providers  │
│ Code execution │            │  Eval / agents  │
└────────────────┘            └─────────────────┘
```

## Frontend

- **Framework:** React 19 with Vite and TypeScript (strict mode)
- **Styling:** Tailwind CSS v4 with CSS custom properties for dark/light themes
- **Routing:** React Router v7 with nested layout routes
- **Data fetching:** TanStack Query with centralized Axios client
- **Structure:** Feature-oriented folders under `src/` — components, pages, routes, hooks, services, types, mocks

The application shell provides a responsive sidebar + header layout. All product modules render placeholder pages in Build 1.

Mock dashboard data lives in `src/mocks/dev-data.ts` and should be removed when real APIs are available.

## Backend

- **Framework:** FastAPI with API versioning under `/api/v1`
- **Layers:**
  - `api/v1/` — HTTP routers (thin controllers)
  - `services/` — business logic
  - `repositories/` — data access (prepared for future use)
  - `schemas/` — Pydantic request/response models
  - `models/` — SQLAlchemy domain models (one file per domain)
  - `core/` — configuration and exception handling
  - `utils/` — shared utilities (Redis, DB checks)

Build 1 endpoints: `GET /health`, `GET /modules`.

## PostgreSQL

- **ORM:** SQLAlchemy 2 async with `asyncpg` driver
- **Migrations:** Alembic configured for async migrations
- **Models:** Base mixins (`UUIDPrimaryKeyMixin`, `TimestampMixin`) ready for domain models

Future domains will add independent model files: `user.py`, `question.py`, `coding_problem.py`, etc.

No production schema is created in Build 1 beyond migration infrastructure.

## Redis

- Connected via `redis.asyncio` on startup
- Build 1 only verifies connectivity (ping)
- Future uses: caching, exam timers, autosave, rate limiting, leaderboard cache, code execution queues

## Future: Judge0

- Configuration: `JUDGE0_URL`, `JUDGE0_API_KEY`
- Service placeholder: `app/services/code_execution/`
- **Critical rule:** Student code MUST NEVER execute inside the FastAPI container
- Future submissions delegate to Judge0 or an equivalent isolated execution service

## Future: LLM Services

- Prompt Engineering evaluation (promptfoo-style patterns)
- AI interview follow-up questions
- RAG and agent evaluation
- Red-team / AI security learning modules

These will be separate service interfaces, not embedded in practice routers.

## Infrastructure

Docker Compose services:

| Service | Port | Purpose |
|---------|------|---------|
| postgres | 5432 | Primary database |
| redis | 6379 | Cache and queues |
| backend | 8000 | FastAPI API |
| frontend | 5173 | Vite dev server |

## Design Principles

1. **Domain isolation** — Each product area gets its own models, services, and routes
2. **No donor repo coupling** — External repos are reference only
3. **No premature features** — Auth, execution, and LLM integration deferred to later builds
4. **API versioning** — All endpoints under `/api/v1`
