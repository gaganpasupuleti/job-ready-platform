# Reproducible preview — PR #24 (`feat/roadmap-ui-clean`)

**PR:** [#24](https://github.com/gaganpasupuleti/job-ready-platform/pull/24) — **not merged**

## 1. Workspaces

| Role | Path | Branch | HEAD (at audit) |
|------|------|--------|-----------------|
| Main (local dev / retro UI) | `c:\Users\Admin\OneDrive\Documents\cursor\New folder (5)` | `feat/official-roadmaps-retro-ui` | `56ba9a676603fcbce6183523306098742ad422d6` |
| PR #24 delivery worktree | `c:\Users\Admin\OneDrive\Documents\cursor\jobready-roadmap-ui-clean` | `feat/roadmap-ui-clean` | `320dac2` → **pending commit** with More menu + handle fix |

### Main workspace — uncommitted (not PR #24)

Modified: UI polish, nav/auth, Power BI lab WIP, `graphValidation.ts` (**untracked** — ad hoc copy; do not treat as delivery).

### Clean worktree — uncommitted (this pass)

- `Masthead.tsx`, `jobready-v4-shell.css` — More dropdown layout + focus/hover
- `graph.ts`, `roadmapHandles.tsx` — React Flow handle id mapping
- `roadmapOfficial.test.ts` — handle mapping test
- E2E PNG artifacts (regenerated locally)

## 2. Preview URLs & processes

| Service | URL | Process | Source |
|---------|-----|---------|--------|
| **PR #24 frontend** | **http://127.0.0.1:5175/** (5174 was busy → Vite auto-increment) | Vite from `jobready-roadmap-ui-clean/frontend` | Delivery branch @ `961a182` |
| Main frontend (unchanged) | http://127.0.0.1:5173/ | Vite from `New folder (5)/frontend` | Retro branch + local edits |
| API (shared) | http://127.0.0.1:8000/ | `uvicorn app.main:app` | `New folder (5)/backend` @ `56ba9a6`, `.venv` Python |

Vite dev proxy (`frontend/vite.config.ts`): `/api` → `http://127.0.0.1:8000` (both frontends).

**Start PR preview (if 5174 free):**

```powershell
cd "c:\Users\Admin\OneDrive\Documents\cursor\jobready-roadmap-ui-clean\frontend"
npm run dev -- --host 127.0.0.1 --port 5174
```

Sign in required for `/roadmaps` (uses live API on 8000 unless mocked).

## 3. `graphValidation.ts`

Tracked on delivery branch since `d9709ea` at:

`frontend/src/features/roadmap-official/graphValidation.ts`

Main workspace copy was only needed because retro branch was missing the file locally; **delivery does not depend on manual copy**.

## 4. Build

```powershell
cd jobready-roadmap-ui-clean\frontend
npm run build   # pass after handle + More menu changes
```

## 5. React Flow handle warnings (#008)

**Cause:** Each roadmap.sh slot (`w1`, `x2`, …) rendered **two** `<Handle>` components with the **same** `id` (source + target). React Flow 12 keeps one handle per id → edges referencing `x2` / `w1` could not attach.

**Fix (no edges dropped):**

- Handles: `w1-s` / `w1-t`, … in `roadmapHandles.tsx`
- Edges: `toFlowEdge()` appends `-s` / `-t` to `sourceHandle` / `targetHandle` in `graph.ts`

**Example (from console on `ai-agents` graph):**

| Edge id (prefix) | sourceHandle | targetHandle |
|------------------|--------------|--------------|
| `xy-edge__Ji35JsKgUQXN4DJGEgTACx2-…` | `x2` → `x2-s` | … |
| `xy-edge__Y8EqzFx3qxtrSh7bWbbV8x2-…` | … | `w1` → `w1-t` |

Re-verify on http://127.0.0.1:5174/roadmaps/ai-agents after login — console should not repeat #008 for handle ids.

## 6. More dropdown (this pass)

- Sectioned **flex** panel (no `display: contents` flattening)
- Per-section **2-column grid**; admin single column
- Soft hover/active; **focus-visible** inset border (not global thick outline)
- Feedback row separated at top

## 7. Verification checklist (same preview)

| Check | How |
|-------|-----|
| Roadmap graph | Login → `/roadmaps/ai-agents` on **5174**; no #008 spam |
| More menu | Open More on Jobs; hover SQL — muted fill, no black pill |
| Mocked e2e | `cd frontend; $env:CI='true'; npx playwright test e2e/roadmap-mock.spec.ts` (starts **5173** by default — use clean server on 5174 or stop 5173) |

## 8. Outstanding

- Port auth-shell + full nav pill styles from main retro workspace into a single PR #24 commit (optional follow-up).
- Main workspace `graphValidation.ts` still untracked on retro — cherry-pick or merge from `feat/roadmap-ui-clean`.
- Live graph parity / validator / assembly endpoint — unchanged from `VISUAL_POLISH_DELIVERY.md`.
