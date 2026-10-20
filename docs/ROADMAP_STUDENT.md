# Student career roadmaps (v1)

## Routes

| Path | Purpose |
|------|---------|
| `/roadmaps` | List published roadmap definitions |
| `/roadmaps/:familySlug` | Interactive map + list (roadmap.sh-style flow) |
| `/dev/roadmap-preview` | Redirects to `/roadmaps/data-engineer` (legacy dev URL) |

Query params on the family page: `?node=<node_key>` (selected node), map/list toggled in UI (stored in `sessionStorage`).

## API

Authenticated student:

- `GET /api/v1/roadmap/catalog`
- `GET /api/v1/roadmap/assembly?family_slug=data-engineer&config_version=2-linked-draft` (version optional; defaults from catalog)

Static JSON lives in `backend/app/data/roadmaps/` until `feature/jobready-role-roadmap-engine-v1` assembly service is merged.

## Navigation

- **More → Career → Career roadmap** → `/roadmaps`
- **Job Readiness** page → link to `/roadmaps`

## Draft honesty

The first shipped assembly (`data-engineer` / `2-linked-draft`) is marked `preview_only` and `student_eligible=false` in JSON. The UI shows a draft banner until a published config replaces it.

## Node destinations

Node resources resolve to existing JobReady routes (`frontend/src/features/roadmap/destinations.ts`): learn materials, courses, SQL problems, projects, etc.
