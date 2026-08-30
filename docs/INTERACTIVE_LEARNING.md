# Interactive Learning (Build 5)

Course → Module → Lesson domain for guided interactive practice. Separate from flat practice paths, but paths can link into courses.

## Domain

- **Course** — published catalog entry (`python-foundations` seeded)
- **Module** — ordered group of lessons
- **Lesson** — types: `concept`, `interactive_code`, `mcq`, `practice`, `checkpoint`

Supporting tables: steps, hints (progressive reveal), doubts (FAQ), resources, attempts, feedback, user progress.

## Lesson workspace

Desktop: progress sidebar + statement/editor split for interactive-code lessons. Mobile: stacked tabs plus an outline drawer.

Interactive lessons save practice attempts without pretending execution passed while Judge0 is off. See `docs/PRACTICE_WORKSPACES.md`.

Tabs:

1. **Statement** — structured JSON blocks (text, code, lists, callouts)
2. **Code** — Monaco editor with starter code (interactive / practice lessons)
3. **Submissions** — attempt history for the lesson
4. **Solution** — gated by `solution_reveal_policy` (default `after_completion`)
5. **Hints** — sequential reveal; unlock can depend on attempt count
6. **Help** — curated doubts + resources (**not** AI Help; no LLM)

Prev / Next navigation and **Mark complete** (seeded Python course sets `completion_requires_submit=False` so Judge0 is optional).

## Progress & locking

- `previous_complete` unlock mode: next lesson stays locked until prior is completed
- Course and lesson progress percent feed Continue Learning on Hub and Dashboard
- Unpublished courses/lessons never appear on student APIs

## Projects foundation

`projects` / modules / tasks with availability flags. `/practice/projects` lists catalog; one sample project is published; other categories may be Coming Soon.

## Admin

Minimal publish/toggle UI at `/admin/courses`. Create/update via `/api/v1/admin/courses`, `/modules`, `/lessons`.

## Security / product rules

- No LLM APIs in the learning UI
- Do not expose locked solutions or hidden coding tests through lesson payloads
- Reuse DSA `CodeEditor` and coding APIs when a lesson links a `coding_problem_id`

## Docs

- [PRACTICE_HUB.md](PRACTICE_HUB.md)
