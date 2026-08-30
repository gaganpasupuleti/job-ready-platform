# Scenario Engine (Build 7)

One **deterministic** scenario engine is shared by Cloud, DevOps, and Cybersecurity. There is **no LLM** and no live infrastructure.

## Tables

- `scenario_challenges` — slug, domain (`cloud` \| `devops` \| `cybersecurity`), type, difficulty, context, evidence JSON, unofficial cert tag, active flag
- `scenario_steps` — prompt, optional snippet, critical flag, weight, explanation
- `scenario_options` — labels; `is_correct` is **admin-only**
- `scenario_submissions` / `scenario_step_answers` — per attempt
- `scenario_progress` — best score, attempt count, mastered vs attempted

Types: `architecture`, `troubleshooting`, `incident_response`, `security_review`, `deployment`, `observability`, `decision_tree`.

Student UI: `/scenarios/:slug` renders evidence as metric/log cards (not raw JSON), step-by-step confirm, score, retry, next scenario. See `docs/PRACTICE_WORKSPACES.md`.

## Scoring

Weighted share of correct steps (0–100). Each missed **critical** step subtracts 10 (floor 0). Mastery default 80. Response includes score, correct decision count, missed critical prompts, and per-step explanations.

## Student API

| Method | Path |
|--------|------|
| GET | `/api/v1/scenarios?domain=` |
| GET | `/api/v1/scenarios/{slug}` (hides `is_correct`) |
| POST | `/api/v1/scenarios/{slug}/submit` |
| GET | `/api/v1/scenario-submissions/{id}` (owner only) |
| GET | `/api/v1/cloud`, `/devops`, `/cybersecurity` and `.../progress` |

Frontend workspace: `/scenarios/:slug`.

## Admin

`/admin/scenarios` create/edit steps, options, scoring text, difficulty, skills via taxonomy elsewhere, publish/unpublish.

MCQs stay in `/admin/questions`.

## Content Factory

Kinds: `scenario_challenge`, `scenario_step`, `scenario_option` (plus `cloud_mcq` / `devops_mcq` / `cybersecurity_mcq`). Validate → stage → review → publish. No auto-publish.
