# PR #24 preview — authoritative table

| Surface | URL | Checkout path | Branch | SHA |
|---------|-----|---------------|--------|-----|
| **Delivery frontend** | http://127.0.0.1:5175/ | `c:\Users\Admin\OneDrive\Documents\cursor\jobready-roadmap-ui-clean\frontend` | `feat/roadmap-ui-clean` | `ca28b41c9317e3ae8332be6132c9ac545a30cf67` |
| **Shared API (dev)** | http://127.0.0.1:8000/ | `c:\Users\Admin\OneDrive\Documents\cursor\New folder (5)\backend` | `feat/official-roadmaps-retro-ui` | `56ba9a6` |
| **Local retro UI (not delivery)** | http://127.0.0.1:5173/ | `New folder (5)\frontend` | `feat/official-roadmaps-retro-ui` | `56ba9a6` + uncommitted WIP |

**Proxy:** Vite `DEV_API_PROXY` / default → `http://127.0.0.1:8000` for `/api/*`.

**Data mode**

| Flow | Mode |
|------|------|
| Signed-in roadmap viewer on 5175 | **Live** API + graphs (requires auth token) |
| `e2e/roadmap-mock.spec.ts` | **Mocked** auth + fixtures |
| `node scripts/audit-roadmap-catalog.mjs` | **Live** graph fetch per slug (401 → `auth` bucket) |

**Uncommitted in delivery worktree (at pass start):** E2E PNG artifacts only unless this commit lands.

**Start delivery frontend**

```powershell
cd "c:\Users\Admin\OneDrive\Documents\cursor\jobready-roadmap-ui-clean\frontend"
npm run dev -- --host 127.0.0.1 --port 5175
```

Do not use port 5173 for PR evidence — that is the retro workspace.
