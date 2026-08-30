# Prompt Challenges

Interactive prompt-engineering practice with a **deterministic evaluator**. Student text is never executed, never sent to a model, and never used to fetch URLs.

## Mental model

Students write a **reusable template** (`{{ticket_text}}`, `{{job_description}}`, …). Each test case injects variables. Checks run on the prompt (and the rendered template), not on LLM output.

## Test vs submit

- **Test** — public cases only, detailed check messages
- **Submit** — public + hidden cases; hidden inputs, expected outputs, and evaluator internals are not returned

Overall score is 0–100 with configurable rubric weights (task accuracy, format, robustness, instruction following, safety, efficiency). These are practice scores, not scientific LLM evals.

Default mastery threshold: **80** (overridable per challenge).

Drafts: `localStorage` key `prompt-draft:{userId}:{challengeId}`.

## Evaluators

`PromptEvaluator` supports: exact match, contains, regex, JSON validity, JSON Schema (subset), classification labels, required/forbidden text, keyword coverage, format markers, variable_used, max length.

Limits (settings): `PROMPT_MAX_CHARS`, `PROMPT_MAX_CASES`, `PROMPT_MAX_REGEX_LENGTH`, `PROMPT_EVALUATION_TIMEOUT_MS`.

## Security

Treat student prompts as untrusted. Do not execute code, render raw HTML, invoke tools, or follow URLs from prompt text. Hidden cases must stay private.

## Admin

`/admin/ai/prompts` — CRUD, public/hidden cases, rubric weights, validate-before-activate.

Invalid challenges cannot be activated.

## Content Factory

`content_kind`: `prompt_challenge`, `prompt_case`, `prompt_rubric`, `ai_mcq`. Flow remains validate → staging → admin review → publish. No auto-publish. No LLM in production.
