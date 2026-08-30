# Projects (Build 5.1)

Guided **Project → Module → Task** tracks. Original Job Ready wording. Engines are reused, not duplicated.

## Hierarchy

```
Project
  └── Module
        └── Task (concept | coding | sql | mcq | checklist | implementation | review)
```

- **coding** tasks link `coding_problem_id` → `/practice/dsa/{slug}`
- **sql** tasks link `sql_problem_id` → `/practice/sql/{slug}`
- **mcq** tasks link `topic_id` → `/practice/mcq?topic=`
- concept / checklist / implementation / review use `/projects/:slug/tasks/:taskId`
- Linked coding/SQL/MCQ/scenario tasks auto-complete when the engine challenge is solved
- Continue Project opens the first incomplete task workspace

See `docs/PRACTICE_WORKSPACES.md`.

## Student routes

| UI | API |
|----|-----|
| `/practice/projects` | `GET /api/v1/projects` |
| `/projects/:slug` (alias `/practice/projects/:slug`) | `GET /api/v1/projects/{slug}` |
| Start / Continue | `POST /api/v1/projects/{id}/start` |
| Mark task complete | `POST /api/v1/projects/{id}/tasks/{task_id}/complete` |

Progress: `not_started` → `in_progress` → `completed`, percent from completed tasks, Continue Project on hub/dashboard.

## Categories seeded

Python, Java, C++, JavaScript, SQL, data analysis, machine learning (design-only), GenAI skeletons (no LLM), DevOps, cloud architecture (no cloud APIs), cybersecurity (defensive review only).

Build 7 wires selected DevOps/Cloud/Cyber projects to MCQ topics and `/scenarios/:slug` checklist tasks (still no live cloud or cluster).

## Admin

`/admin/projects`, `/admin/projects/new`, `/admin/projects/:id/edit`

API: `GET/POST /api/v1/admin/projects`, `PATCH /api/v1/admin/projects/{id}`, modules and tasks.

## Related

[PRACTICE_HUB.md](PRACTICE_HUB.md) · [CONTENT_FACTORY.md](CONTENT_FACTORY.md) · [INTERACTIVE_LEARNING.md](INTERACTIVE_LEARNING.md)
