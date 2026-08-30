# Practice workspaces (Build 7.1)

Student challenge screens share one practice language: header (back, previous/next, title, difficulty, status, bookmark, reset, primary action), tabs, resizable desktop split, mobile Problem | Code | Output tabs, and consistent empty/error/loading/success states.

Shared UI lives in `frontend/src/components/practice-workspace/PracticeWorkspace.tsx`.

## Status badges

Not Started, Attempted, In Progress, Solved, Completed, Mastered, Locked.

## Execution

- **SQL** uses the isolated sandbox. Run shows output; Submit compares expected rows. Hidden expected rows are never shown on wrong answers.
- **Coding / DSA** keeps Run/Submit ready, but with `JUDGE0_ENABLED=false` they stay disabled and show: “Code execution is temporarily unavailable…” Drafts, samples, hints, submissions, and navigation still work. Do not fake results.
- **Learn interactive-code** uses **Save Practice Attempt** (not Run) while execution is off. Attempts store code, language, and timestamp with `is_correct=false`. Linked coding problems open the graded DSA workspace.

## SQL / Coding navigation

`GET /api/v1/sql/problems/{id}/navigation`  
`GET /api/v1/coding/problems/{id}/navigation`

Returns previous/next, position, total, and navigator items.

Keyboard: Ctrl/Cmd+Enter run/test, Ctrl/Cmd+Shift+Enter submit (when execution is enabled).

## Projects

Task workspace: `/projects/:slug/tasks/:taskId`.

- Concept: manual complete is allowed.
- Coding / SQL / MCQ / Scenario: open the existing engine. Completing the linked challenge auto-completes the task. No extra Mark Complete.
- Checklist / review / implementation: persist `checklist_state` on the server; all required items complete the task.
- Continue Project routes to the first incomplete task workspace.

## Path completion

`UserPracticePathItemProgress` is unique per `(user_id, item_id)`. Completing the same item again does not increase percent.

## Mistake book

Not built. Result payloads from MCQ, coding, SQL, prompt, and scenario remain available for later aggregation.

## Retry Incorrect (MCQ)

Deferred to a later practice polish build.
