# Donor Repositories

External open-source repositories used as **reference implementations only**. We build our own architecture and do not merge donor codebases.

## 1. CodeLeap

| Field | Value |
|-------|-------|
| Repository | [sanketsingh01/CodeLeap](https://github.com/sanketsingh01/CodeLeap) |
| Purpose | Coding practice UX patterns |
| Concepts to reuse | Problem pages, progress UI, Monaco editor integration patterns, submissions flow, difficulty/category UI |
| License | Verify before any code reuse |
| Code reuse | Reference patterns; implement independently |

## 2. ExamHall (online-exam-system)

| Field | Value |
|-------|-------|
| Repository | [KhushiToshniwal/online-exam-system](https://github.com/KhushiToshniwal/online-exam-system) |
| Purpose | Online examination system concepts |
| Concepts to reuse | Question banks, MCQ exams, coding questions, timers, autosave, exam attempts, hidden test cases, scoring |
| License | **NOT CONFIRMED** |
| Code reuse | **REFERENCE ONLY — LICENSE NOT CONFIRMED** |

## 3. GrillKit

| Field | Value |
|-------|-------|
| Repository | [GrillKit/grillkit](https://github.com/GrillKit/grillkit) |
| Purpose | Interview and assessment flow |
| Concepts to reuse | Interview flow, theory questions, coding interviews, AI follow-up questions, scoring, public/hidden test patterns, Judge0 integration concepts |
| License | Verify before any code reuse |
| Code reuse | Reference patterns; implement independently |

## 4. promptfoo

| Field | Value |
|-------|-------|
| Repository | [promptfoo/promptfoo](https://github.com/promptfoo/promptfoo) |
| Purpose | LLM and prompt evaluation |
| Concepts to reuse | Prompt Engineering challenges, LLM evaluation, RAG evaluation, agent evaluation, AI security/red-team learning |
| License | MIT (verify current license) |
| Code reuse | Reference evaluation architecture; do not embed promptfoo directly |

## 5. jobhive

| Field | Value |
|-------|-------|
| Repository | [shouqatazeez/jobhive](https://github.com/shouqatazeez/jobhive) |
| Purpose | Jobs portal UX |
| Concepts to reuse | Job browsing, filtering, job details, applications, application status tracking |
| License | Verify before any code reuse |
| Code reuse | Reference UX patterns; implement independently |

## 6. Judge0

| Field | Value |
|-------|-------|
| Repository | [Judge0/judge0](https://github.com/judge0/judge0) |
| Purpose | Isolated code execution |
| Concepts to reuse | Sandboxed compilation and execution, language support, submission result format |
| License | GNU GPL v3 (Judge0 CE) — verify deployment model |
| Code reuse | Deploy as separate service; integrate via API only |

## Policy

1. Never copy-paste donor code without license verification
2. Never combine donor repos into one codebase
3. Study concepts, design our own modules
4. ExamHall is strictly reference-only until license is confirmed
