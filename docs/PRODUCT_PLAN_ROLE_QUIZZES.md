# Product plan — role roadmaps & quiz banks (deferred)

**Status:** Roadmaps ship first (see `docs/ROADMAP_STUDENT.md`). This doc captures the quiz/assessment work discussed 2026-10-20 — **not implemented yet**.

## Goals (later phases)

1. **Role-family quizzes** — Applying as Data Analyst / Python dev opens exams tagged to that `role_family` (same slugs as jobs: `data-analyst`, `python-dev`, …).
2. **Experience bands** — Intern/fresher, 3–5 years, 5+ years as exam profiles (not only job listing filters).
3. **Weekly rotation** — `content/batches/{year}-W{nn}/` publishes new questions; packs define role × band × week.
4. **Formats** — MCQ (existing session engine), SQL (sandbox-linked items), fill-in-the-blank for Python (extend `practice_service` + session UI).
5. **Bank size** — Target ~500 questions per **leaf topic** from an external syllabus repo (single source of truth); shared pools across roles (e.g. SQL joins for analyst + engineer).
6. **Honest catalog** — Hide topics with `question_count === 0`; no empty “for show” tiles.

## Current baseline (before quiz phase)

- One MCQ session engine (`/api/v1/practice/*`).
- ~106 batch questions, 8 studio packs, 345 taxonomy topics (mostly empty).
- `families[]` on packs/materials; practice catalog does **not** filter by family.
- Roadmap v1: interactive map at `/roadmaps/:familySlug` (draft `data-engineer` first).

## Recommended implementation order

| Phase | Deliverable |
|-------|-------------|
| **R1** (now) | Student roadmaps UI + `GET /api/v1/roadmap/*`; merge `feature/jobready-role-roadmap-engine-v1` for live assembly |
| **R2** | Import syllabus from external topics repo; replace ad-hoc taxonomy for one vertical |
| **Q1** | `GET /practice/catalog?family=&band=` + `/assessments/role/:family` hub |
| **Q2** | Weekly batch contract + admin publish; role exam packs |
| **Q3** | Fill-blank + SQL-in-session; 500/topic quotas per leaf |

## Entry points (when quiz phase ships)

- `/assessments/role/:family` — pick band → weekly exam or topic practice
- `/roadmaps/:family` — node links to materials, SQL, packs, then role exams
- `/jobs/:slug` — practice gaps → roadmap node or role exam
- `/readiness` — CTA to roadmap + recommended weekly exam

## Branches / references

- `feature/jobready-roadmap-frontend-v1` — map/list UI (merged into main app)
- `feature/jobready-role-roadmap-engine-v1` — DB definitions, assembly service, career goal API
- `backend/design-reference/developer-roadmap-master` — reference topic graphs (license: roadmap.sh community repo)

## Open decisions

- [ ] External syllabus repo URL and first role (Python vs Data Analyst)
- [ ] Exact experience band labels
- [ ] Whether roadmap.sh UI is forked vs JobReady `RoadmapMap` component (current: JobReady component, roadmap.sh-like flow)
