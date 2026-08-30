# Release QA Checklist (Build 7.2)

Use this before tagging a browser-tested release. Prefer Playwright where automated; check the rest manually.

## Auth

- [ ] Register with valid data reaches authenticated app
- [ ] Login with valid credentials reaches dashboard
- [ ] Invalid password shows error and stays on `/login`
- [ ] Logout clears token; `/practice` redirects to `/login`
- [ ] Logged-out deep link to protected route redirects to login
- [ ] Reload after login remains authenticated
- [ ] Expired/401 clears token and returns to login (no loop on login itself)

## Dashboard

- [ ] `/` loads without fatal console errors
- [ ] Continue Learning appears when progress exists
- [ ] Live SQL / coding / AI / project stats render
- [ ] No fake readiness values, NaN, undefined, or `[object Object]`

## Practice Hub

- [ ] `/practice` loads path cards and sections
- [ ] Search finds known path; nonsense query shows empty state
- [ ] Available path opens; Coming Soon does not navigate incorrectly
- [ ] Links to Projects / SQL / DSA / MCQ work

## MCQ

- [ ] Practice mode: question, options, submit, explanation, next/prev, bookmark, clear selection
- [ ] Session completes to results with score breakdown
- [ ] Exam mode: timer, navigator, mark for review, confirm submit
- [ ] Path item completion is idempotent (percent does not double-count)
- [ ] Retry Incorrect deferred (document only)

## Coding

- [ ] Problem statement, languages, editor, samples, navigator, hints
- [ ] With `JUDGE0_ENABLED=false`: unavailable banner, Run/Submit disabled, no fake results
- [ ] Draft persists per language; reset restores starter

## SQL

- [ ] Problem, schema, sample output, editor, Run/Submit, navigator
- [ ] Valid Run shows rows and leaves button as Run (not stuck on Running…)
- [ ] Syntax error recovers; editor content remains
- [ ] Blocked DML/DDL rejected with clear safety message
- [ ] Wrong submit: feedback without exposing hidden expected rows
- [ ] Accepted submit: Accepted state, solution policy, submissions tab, persists on reload
- [ ] Draft persistence + Reset confirm/cancel
- [ ] Ctrl/Cmd+Enter Run; Ctrl/Cmd+Shift+Enter Submit

## Learn

- [ ] Course list → detail → modules/lessons/status
- [ ] Concept lesson: content, hints, complete, progress
- [ ] Interactive lesson: statement + editor; Save Practice Attempt (not Run); history updates
- [ ] Mobile 390×844: no page overflow; outline usable

## Projects

- [ ] Overview, skills, roadmap, Continue Project
- [ ] Checklist: item persistence; incomplete does not complete task; all required completes
- [ ] SQL-linked task syncs after accepted SQL
- [ ] MCQ-linked task syncs per current topic-level behavior
- [ ] Scenario-linked task syncs when seeded
- [ ] Continue Project advances to next incomplete task
- [ ] Project completion summary + Start Another Project

## AI / Prompts

- [ ] Challenge workspace: requirements, hints, editor, preview, mastery
- [ ] Test returns score/rubric without hidden case leakage
- [ ] Submit counts hidden cases without exposing inputs
- [ ] Draft + Reset; keyboard shortcuts without double submit
- [ ] `/ai/ml` Coming Soon (not 404)
- [ ] `/ai/rag` only surfaces RAG/retrieval/vector topics
- [ ] AI track smoke routes load

## Cloud / DevOps / Cyber / Scenarios

- [ ] Track and progress pages load
- [ ] Scenario evidence cards render (not raw JSON dump)
- [ ] Decision → explanation → complete → score / Retry / Next

## Bookmarks

- [ ] Bookmark MCQ / coding / SQL / prompt
- [ ] Appears on `/bookmarks`; navigate back; unbookmark persists after refresh

## Interviews (smoke only — Build 8 not started)

- [ ] `/interviews` loads approved questions / empty state
- [ ] Expand shows expected answer and key points

## Placeholders

- [ ] `/company-prep`, `/assessments`, `/contests`, `/jobs*`, `/readiness`, `/mistakes`, `/leaderboard` show clean placeholders (no 404)

## Admin

- [ ] Admin login can open questions/sql/coding/content/paths/courses/projects/ai/scenarios lists
- [ ] Student cannot access admin tooling
- [ ] Optional: create/edit/delete isolated MCQ with E2E marker
- [ ] SQL Validate works on seeded problem
- [ ] Prompt validation blocks invalid activation

## Responsive

- [ ] Desktop 1440×900, laptop 1280×720, tablet 768×1024, mobile 390×844
- [ ] Sidebar menu opens/closes on mobile; workspaces usable
- [ ] No full-page horizontal overflow (local panels may scroll)

## Deployment

- [ ] SPA fallback (`serve -s` / equivalent) so deep links survive refresh
- [ ] CORS + `VITE_API_BASE_URL` correct
- [ ] `JUDGE0_ENABLED=false` unless Judge0 VM is ready
- [ ] SQL sandbox vars set; Redis optional behavior understood
- [ ] `VITE_ENABLE_DEV_LOGIN=false` in production builds
- [ ] Production `JWT_SECRET_KEY` is not the default
- [ ] `python scripts/smoke.py --base-url <api>` passes
- [ ] Unknown route shows Page not found with Dashboard / Practice Hub links
