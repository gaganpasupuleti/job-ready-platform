# Responsive v5 — frontend notes

Branch: `feature/jobready-frontend-responsive-v5`  
Worktree only. Backend code was not changed.

## What this pass uses

- Practice destinations keep existing routes: `/practice/aptitude`, `/practice/sql`, `/practice/dsa`, `/practice/coding`, `/practice/mcq`, `/practice/projects`.
- Subject names come from the catalog response (`domains[].categories[]`). The client does not invent subjects.
- Progress totals stay on the pages that already call coding and SQL progress. Destination navigation does not derive catalog-wide counts from a loaded page of problems.
- Courses and mistake review are linked only at existing routes (`/learn`, `/mistakes`). SQL mistake CTAs remain the live retry path.
- Python playground still uses `GET /coding/execution-status`, local drafts, and `useLockExecutionShortcuts`. Run stays disabled when `available !== true`.
- Prompt A’s unfinished frontend diff did not include Playground changes. The playground already on this base was kept.

## Missing backend dependencies

| Need | What exists | Do not fake on the client |
|------|-------------|---------------------------|
| Question inventory per subject or topic | Catalog returns names and slugs only | Do not show question counts until the catalog includes them |
| Unified practice-destination payload | Separate catalog, coding progress, and SQL progress calls | Destination labels are routes, not a new aggregate |
| Dedicated coding topics endpoint | `CodingProgressSummary.topics` is built from `list_problems(limit=500)` | If `total_problems` exceeds returned items, topic chips are incomplete; the topic-slug field remains the fallback |
| Next recommended item inside a quiz subject | Session create requires a chosen topic | The next action is `Start {selected topic}`, not an invented recommendation |
| Course-to-topic deep links for every quiz subject | Practice paths may include `external_route`; lessons have their own routes | Do not synthesize a course link when the path does not provide one |
| Playground SQL execution | SQL has its own workspace and sandbox status | The Python playground must not call SQL run/submit or unlock Python when Judge0 is unavailable |
