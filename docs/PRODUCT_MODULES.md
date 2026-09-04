# Product Modules

Status as of MVP hardening (Build 10 + release audit).

Legend: **Live** = student-usable · **Partial** = usable with known limits · **Future** = placeholder / not shipped

## Practice

| Module | Route | Status |
|--------|-------|--------|
| Practice Hub | `/practice` | Live |
| Aptitude / CRT | `/practice/aptitude` | Live |
| DSA | `/practice/dsa` | Live |
| Coding Practice | `/practice/coding` | Partial — editor live; Judge0 execution disabled |
| SQL Practice | `/practice/sql` | Live — requires SQL sandbox |
| Technical MCQs | `/practice/mcq` | Live |

## Learn & Projects

| Module | Route | Status |
|--------|-------|--------|
| Courses / Learn | `/learn` | Live |
| Projects | `/practice/projects`, `/projects/:slug` | Live |

## AI Era

| Module | Route | Status |
|--------|-------|--------|
| AI Home | `/ai` | Live |
| Generative AI / Prompt / RAG / Agents | `/ai/*` | Live — deterministic prompts, no LLM |
| Prompt workspace | `/ai/prompts/:slug` | Live |

## Infrastructure

| Module | Route | Status |
|--------|-------|--------|
| Cloud | `/cloud` | Live |
| DevOps | `/devops` | Live |
| Cybersecurity | `/cybersecurity` | Live |
| Scenarios | `/scenarios/:slug` | Live |

## Career / Interviews

| Module | Route | Status |
|--------|-------|--------|
| Interview hub | `/interviews` | Live |
| Packs / sessions / review | `/interviews/*` | Live — self-review, not AI scoring |
| Company prep | `/company-prep` | Live |
| Assessments | `/assessments` | Future |
| Contests | `/contests` | Future |

## Jobs

| Module | Route | Status |
|--------|-------|--------|
| Jobs portal | `/jobs` | Live |
| Recommended | `/jobs/recommended` | Live — relevance, no match % |
| Saved / Applications | `/jobs/saved`, `/jobs/applications` | Live |
| Admin jobs / CSV | `/admin/jobs` | Live |

## Progress / Readiness

| Module | Route | Status |
|--------|-------|--------|
| Readiness | `/readiness` | Live |
| Readiness skills | `/readiness/skills` | Live |
| Mistake Book | `/mistakes` | Live |
| Bookmarks | `/bookmarks` | Live / Partial by domain |
| Leaderboard | `/leaderboard` | Future |
| Admin readiness | `/admin/readiness` | Live |

## Dashboard

| Feature | Status |
|---------|--------|
| Readiness / recommendations cards | Live (API-backed) |
| Practice / jobs shortcuts | Live |
| Contests / assessments widgets | Future / hidden |

## Explicit non-goals (MVP)

- Hiring probability or “chance of getting hired”
- External LLM execution
- Live Judge0 coding (until separately provisioned)
- Payments, community, certificates, live classes
