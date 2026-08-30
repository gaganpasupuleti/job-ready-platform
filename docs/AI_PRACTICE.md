# AI Practice (Build 6)

Job-ready GenAI practice **without any external LLM API**. There is no OpenAI, Gemini, Claude, Groq, or hosted inference in this build.

## What students get

| Surface | Engine |
|---------|--------|
| `/ai` dashboard | Progress from MCQ attempts + prompt challenges |
| `/ai/genai`, `/ai/rag`, `/ai/agents`, `/ai/mcp`, `/ai/tool-calling`, `/ai/evaluation`, `/ai/security`, `/ai/system-design` | **Universal MCQ engine** (`PracticeCatalog`, domain `ai`) |
| `/ai/prompt-engineering` | Theory MCQs |
| `/ai/prompt-engineering/challenges` | Dedicated **prompt challenge** engine |
| `/ai/progress` | Track-level accuracy and mastery (not a global Job Readiness Score) |

Practice Hub paths (`path_type=ai`) reuse the existing path engine: Generative AI, RAG, Prompt Engineering, AI Agents, MCP, AI Security.

The prompt workspace uses the shared practice shell (tabs, rubric visualization, next challenge). See `docs/PRACTICE_WORKSPACES.md`. `/ai/ml` is a Coming Soon placeholder until a dedicated ML track exists.

## What this build does not do

- No conversational chatbot or mock-interview LLM judge
- No live agents, tool execution, MCP runtime, embeddings service, or vector database
- No job matching or global readiness score

Promptfoo may be used later as an optional adapter. It is **not** required.

## APIs

Student: `/api/v1/ai/home`, `/progress`, `/prompts`, `/prompts/{slug}`, `/prompts/{slug}/test`, `/submit`, `/prompt-submissions`, `/prompt-bookmarks`

Admin: `/api/v1/admin/ai`, `/admin/ai/prompts`, validate endpoint

AI MCQs are authored in the existing `/admin/questions` UI.

See [PROMPT_CHALLENGES.md](PROMPT_CHALLENGES.md) for the interactive prompt workspace.
