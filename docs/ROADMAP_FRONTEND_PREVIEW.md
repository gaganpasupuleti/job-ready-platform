# JobReady interactive roadmap frontend (v1)

**Branch:** `feature/jobready-roadmap-frontend-v1`  
**Worktree:** `../jobready-roadmap-fe`  
**Base:** `origin/master` @ `31d9a25`  
**Fixture source:** backend `feature/jobready-role-roadmap-engine-v1` commit `850b79f`  
**Sanitized fixture:** `frontend/src/features/roadmap/fixtures/de-linked-draft.assembly.json`

## Student routes (production)

- `/roadmaps` — catalog
- `/roadmaps/:familySlug` — map + list (e.g. `/roadmaps/data-engineer`)
- `/dev/roadmap-preview` — DEV redirect to `/roadmaps/data-engineer`

See `docs/ROADMAP_STUDENT.md`.

Dev server default port: **5185** (avoids colliding with other JobReady previews on 5173).

```bash
cd frontend
npm install
npm run dev
# open http://localhost:5185/dev/roadmap-preview
```

## Contract adapter

`frontend/src/features/roadmap/adapter.ts` loads the fixture in DEV.  
Replace with authenticated `loadRoadmapAssemblyFromApi` when the backend endpoint exists.

### Backend dependency (not in this branch)

Authenticated student/internal assembly endpoint, e.g.  
`GET /api/v1/roadmap/assembly?family_slug=&config_version=`  
returning the Phase 5 `RoadmapAssembly` shape. Until then, only the DEV fixture is available.

## Resource destinations

| Export type | FE route | Notes |
|-------------|----------|-------|
| `learning_material` | `/learn/materials/:key` | Verified for `da-sql-filter-agg`, `de-python-validation`, … |
| `sql_problem` | `/practice/sql/:slug` | Assessed practice — **not** `/practice/playground/sql` |
| `course` | `/learn/courses/:slug` | e.g. `python-foundations` |
| `course_lesson` | needs course+module | Fixture-local map for `what-is-python` only |
| `project` | `/projects/:slug` | e.g. `sql-ecommerce-analytics` |
| `coding_problem` | unresolved by slug | Workspace uses UUID (`/practice/dsa/:id`); Run/Submit may be `execution_unavailable` |

Opening a resource does **not** mark the node complete.

## Honest draft flags

Rendered from fixture: `preview_only`, `student_eligible=false`, curriculum incomplete, `production_unset_v0`.
