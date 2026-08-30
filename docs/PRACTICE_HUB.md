# Practice Hub (Build 5)

Student-facing catalog for guided practice paths, courses, and projects. Original Job Ready content — not a CodeChef (or other platform) clone.

## Student routes (frontend)

| Route | Purpose |
|-------|---------|
| `/practice` | Practice Hub: search, category nav, Continue Learning, Recently Practiced, recommended |
| `/practice/paths/:slug` | Path detail with sections/items |
| `/practice/projects` | Projects catalog |
| `/projects/:slug` | Project workspace (alias `/practice/projects/:slug`) |
| `/learn` | Interactive courses list |
| `/learn/courses/:slug` | Course outline |
| `/learn/courses/:course/:module/:lesson` | Lesson workspace |

Existing engines stay at `/practice/dsa`, `/practice/sql`, `/practice/mcq`, `/ai`, `/cloud`, `/devops`, `/cybersecurity`.

## Student API

| Method | Path |
|--------|------|
| GET | `/api/v1/practice-hub` |
| GET | `/api/v1/paths`, `/api/v1/paths/{slug}` |
| GET | `/api/v1/courses`, `/api/v1/courses/{slug}` |
| GET | `/api/v1/courses/{course}/modules/{module}/lessons/{lesson}` |
| POST | `/api/v1/lessons/{id}/start`, `/complete`, `/attempt`, `/feedback` |
| GET | `/api/v1/projects`, `/api/v1/projects/{slug}` |
| POST | `/api/v1/projects/{id}/start`, `/api/v1/projects/{id}/tasks/{task_id}/complete` |
| POST | `/api/v1/paths/{id}/start`, `/api/v1/paths/{id}/items/{item_id}/complete` |
| GET | `/api/v1/learning/continue` |
| GET | `/api/v1/practice/search?q=` |

## Path model

Reusable `practice_paths` with typed sections/items. Item types can reference coding problems, SQL problems, MCQs, courses/lessons, projects, or external routes. Availability is `available` or `coming_soon` (no fake solved counts).

Hub section keys:

- Programming Languages
- Projects
- Beginner DSA
- Data Structures
- Algorithms
- Difficulty Paths
- Interview Questions
- Company Paths
- Other Practice Paths
- AI Practice

Company paths include explicit disclaimer copy: community-curated skill patterns, original content, not affiliated with the company.

Build 6 adds `path_type=ai` paths (Generative AI, RAG, Prompt Engineering, Agents, MCP, AI Security) that link MCQ topics and prompt-challenge routes. See [AI_PRACTICE.md](AI_PRACTICE.md).

## Admin

- `/admin/practice-paths` — list / toggle active
- API: `/api/v1/admin/practice-paths`, `/api/v1/admin/courses`, modules, lessons

## Seed

```bash
cd backend
python -m app.seed.runner
# or
python -c "import asyncio; from app.seed.learn_data import seed_learn_content; asyncio.run(seed_learn_content())"
```

Idempotent by slug. Migration: `006_build5` (`alembic upgrade head`).

See also [PROJECTS.md](PROJECTS.md) for Project → Module → Task and engine reuse.

- [INTERACTIVE_LEARNING.md](INTERACTIVE_LEARNING.md) — courses, lessons, workspace
- Content Factory may later publish into `ContentType` values `course`, `lesson`, `practice_path`, `project`
