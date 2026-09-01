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

## SQL Practice Engine (Build 4 / 4.1)

- **Models:** `SqlProblem`, tables/columns/seed rows, expected results, submissions, progress
- **Sandbox boundaries:** Application DB ≠ Sandbox Admin ≠ Sandbox Runner (separate credentials/pools)
- **Validation:** sqlglot AST (rejects mutating CTEs); DB read-only transaction + role permissions
- **Student API:** `/api/v1/sql/*`
- **Admin API:** `/api/v1/admin/sql/*`
- Docs: [SQL_PRACTICE.md](SQL_PRACTICE.md)

## Interview Practice Engine (Build 8) — detail

- **Content (reused):** `interview_questions`, `interview_answer_points`, packs/mappings, Content Factory approval
- **Session state:** `interview_sessions`, `interview_session_questions`, `interview_question_notes`, `interview_question_reviews` (`011_build8`)
- **Modes:** study / mock / rapid_review — mock hides expected answer until reveal
- **Scoring:** self-review only (key-point coverage, confidence, self-rating) — **no LLM**
- **Student API:** `/api/v1/interview/*` (content), `/api/v1/interviews/*` (sessions/hub/company-prep)
- **Admin API:** `/api/v1/admin/interviews/packs`
- Docs: [INTERVIEW_PRACTICE.md](INTERVIEW_PRACTICE.md)

## Jobs Portal (Build 9)

- **Tables:** expanded `jobs`, `job_sources`, `job_skills`, `job_role_mappings`, `saved_jobs`, `job_applications`, ingestion runs/errors
- **Reuse:** `companies`, `skills`, `job_roles`, `users`
- **No** readiness score or match % (Build 10)
- Student API: `/api/v1/jobs`, `/api/v1/applications`
- Admin: `/api/v1/admin/jobs` (CSV import validate → confirm)
- Docs: [JOBS.md](JOBS.md)

## Coding Practice Engine (Build 3 / 3.1)

- **Models:** `CodingProblem`, `CodingTestCase`, `CodingSubmission`, progress and bookmarks
- **Execution:** Judge0 HTTP client with mock/disabled fallbacks; never runs student code in FastAPI
- **Security:** Run uses public tests only; submit hides hidden test I/O from responses
- **Languages:** Centralized in `app/services/code_execution/languages.py` (71 Python, 62 Java, 54 C++, 63 JS)
- **Student API:** `/api/v1/coding/*` — problems, run/submit, submissions, progress, bookmarks, execution status
- **Admin API:** `/api/v1/admin/coding/*` — CRUD for problems and test cases

## MCQ Practice & Exam Mode (Build 3.1)

- **Practice sessions** with feedback; **exam sessions** with duration, expiry, autosave, navigator
- **Bookmarks** for MCQ questions and coding problems (polymorphic `bookmarks` table)
- **Admin MCQ edit** via `PUT /api/v1/admin/questions/{id}`

## Judge0 Integration

- Configuration: `JUDGE0_URL`, `JUDGE0_AUTH_HEADER`, `JUDGE0_AUTH_TOKEN`, polling + platform max limits
- Service: `app/services/code_execution/` — interface, Judge0 HTTP client (batch/poll), mock, disabled
- Student code **never** runs inside FastAPI; only Judge0 workers execute untrusted code
- Host Judge0 on a privileged Linux VM (`infra/judge0/`, image `judge0/judge0:1.13.1`) — see [JUDGE0_DEPLOYMENT.md](JUDGE0_DEPLOYMENT.md)
- Job Ready Redis is used only for rate/concurrency coordination — not Judge0's Redis
- **Critical rule:** Student code MUST NEVER execute inside the FastAPI container

## Practice Hub & Interactive Learning (Build 5)

- **Models:** `PracticePath` (+ sections/items), `Course` / `CourseModule` / `CourseLesson` (+ hints, doubts, resources, attempts, feedback), `Project` (+ modules/tasks), user progress tables
- **Migration:** `006_build5`
- **Service:** `app/services/learn_service.py` (`LearnService`, `LearnAdminService`)
- **Student API:** `/api/v1/practice-hub`, `/paths`, `/courses`, `/lessons/*`, `/projects`, `/learning/continue`, `/practice/search`
- **Admin API:** `/api/v1/admin/practice-paths`, `/admin/courses`, modules, lessons
- **Frontend:** `/practice` hub, `/practice/paths/:slug`, `/learn/*` lesson workspace, `/practice/projects`, admin pages
- Docs: [PRACTICE_HUB.md](PRACTICE_HUB.md), [INTERACTIVE_LEARNING.md](INTERACTIVE_LEARNING.md), [PROJECTS.md](PROJECTS.md), [PRACTICE_WORKSPACES.md](PRACTICE_WORKSPACES.md)
- **Build 7.1:** Shared student workspaces; `010_build71` (`user_practice_path_item_progress`, project `checklist_state`, optional coding hints/solution JSON); SQL/coding navigation endpoints; linked project task auto-complete

## AI Practice (Build 6)

- **MCQs:** Same universal question engine and taxonomy domain `ai` (no second MCQ stack)
- **Prompt challenges:** Separate tables (`prompt_challenges`, cases, submissions, progress) and `PromptEvaluator` — deterministic, no model provider
- **Student API:** `/api/v1/ai/*` · **Admin:** `/api/v1/admin/ai/*`
- **Frontend:** `/ai`, track pages, prompt workspace, `/ai/progress`, `/admin/ai`
- Docs: [AI_PRACTICE.md](AI_PRACTICE.md), [PROMPT_CHALLENGES.md](PROMPT_CHALLENGES.md)
- Migration: `008_build6`

## Cloud, DevOps, Cybersecurity (Build 7)

- **MCQs:** Universal question engine; taxonomy domains `cloud`, `devops`, `cybersecurity`
- **Scenarios:** Shared deterministic engine (`scenario_*` tables) — no LLM, no cloud/K8s/SIEM APIs
- **Student API:** `/api/v1/cloud`, `/devops`, `/cybersecurity`, `/scenarios`
- **Admin:** `/api/v1/admin/cloud|devops|cybersecurity`, `/admin/scenarios`
- Docs: [CLOUD_PRACTICE.md](CLOUD_PRACTICE.md), [DEVOPS_PRACTICE.md](DEVOPS_PRACTICE.md), [CYBERSECURITY_PRACTICE.md](CYBERSECURITY_PRACTICE.md), [SCENARIO_ENGINE.md](SCENARIO_ENGINE.md)
- Migration: `009_build7`

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
