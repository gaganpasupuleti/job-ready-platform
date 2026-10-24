# PR #24 — pilot release record

**PR:** https://github.com/gaganpasupuleti/job-ready-platform/pull/24 (**merged**)  
**Merge SHA:** `ecc8d5176cf1085bc20b1402b865a92d0f3efcb0` (`ecc8d51`)  
**Release branch commits:** `53363b8` (AUTH preview fix) + `e5b821d` (audit) on `feat/roadmap-ui-clean`  
**Master CI (post-merge):** https://github.com/gaganpasupuleti/job-ready-platform/actions/runs/40076839905 — **success**  
**PR CI (release code):** https://github.com/gaganpasupuleti/job-ready-platform/actions/runs/40075071754 — **success** (`53363b8`)

## Pilot limitations (accepted — track as follow-up)

| Item | Status |
|------|--------|
| **data-analyst** VLOOKUP/HLOOKUP orphan subtopic on canvas | Accepted — search + article work; no invented edge |
| **code-review** id-keyed article gap | Accepted — truthful unavailable content |
| **Article sampling** | Not full corpus — one node per slug in audit |

## Verification completed (pre-production)

| Check | Result | Evidence |
|-------|--------|----------|
| Diff since `dd289ff` | Doc-only `e62b8b6` then AUTH code `53363b8` | Git history |
| Preview surface smoke | **3/3 pass** | `docs/ci-evidence/release-smoke-preview-post-syllabus-local.json` |
| Preview AUTH-01 (registration closed) | **pass** | `docs/ci-evidence/release-smoke-preview-auth-local.json` — pre-provision via `provision_auth01_users.py`; prior full-script failure documented |
| Contrast / UI (mocked) | **42/42 pass** | `docs/ci-evidence/contrast-local-compositing-summary.json` |
| Article audit (sampled) | **92/93** | `docs/ci-evidence/article-audit-post-syllabus-summary.json` |
| Syllabus bundle | In repo @ `e906c5f60c2e72623a73cce4bea51153b319c0d8` | `docs/ROADMAP_SYLLABUS_CONTENT.md` |

## Railway production deploy

| Item | Value |
|------|--------|
| **Frontend URL** | https://frontend-production-f65c0.up.railway.app |
| **Backend URL** | https://backend-production-a0c9.up.railway.app |
| **Pre-deploy frontend bundle** | `assets/index-BwfzyI4L.js` (no `ors-canvas` / official roadmap strings) |
| **Pre-deploy backend** | `GET /api/v1/roadmap/*` → **404** (routes not on running revision) |
| **Pre-deploy API smoke** | `scripts/smoke.py` — **PASSED** (health, modules, SQL status) |
| **Deploy status** | **Not completed from this agent** — `railway` CLI unauthorized; MCP OAuth timed out. **Merge to `master` alone did not update production** (no auto-deploy observed). |

### Required operator steps to finish deploy

1. `railway login` (or set `RAILWAY_TOKEN` for CI/automation).
2. Link **production** project/environment; confirm services **frontend** + **backend** track **`master`** @ `ecc8d51` (or redeploy both from latest `master`).
3. **Frontend build args:** `VITE_API_BASE_URL=https://backend-production-a0c9.up.railway.app`, `VITE_ENABLE_DEV_LOGIN=false`.
4. **Backend:** bundled `backend/app/data/roadmap-syllabus/` in image; leave `ROADMAP_CONTENT_ROOT` unset unless a populated override exists; confirm `CORS_ORIGINS` includes frontend origin.
5. **Migrations:** follow `docs/JOBS_PILOT_RELEASE.md` — no new roadmap-only migration in PR #24; run `alembic upgrade head` only if production is behind existing chain.
6. **Do not** run E2E seeds against production.

### Rollback (before/after deploy)

Record Railway **deployment IDs** for frontend and backend immediately before redeploy. Rollback = redeploy the previous successful deployment for each service (Railway dashboard → service → Deployments → Redeploy). Application DB rollback = restore pre-migration backup per `docs/JOBS_PILOT_RELEASE.md` if a migration was applied.

## Live verification (pending deploy)

After frontend/backend revisions show `ecc8d51` (or newer containing PR #24):

- [ ] Frontend bundle includes roadmap UI (`ors-canvas` or `/roadmaps` route).
- [ ] `GET /api/v1/roadmap/catalog` authenticated → 200.
- [ ] Login/logout with **production-authorized** test account (`PASSWORD_LOGIN_EMAILS` / Google).
- [ ] Jobs save/unsave; roadmap catalog + sample article; library; mobile nav.
- [ ] Logs: no sustained 5xx on roadmap or auth paths.

**Note:** `e2e.student@jobready.dev` is **not** valid on production (login 401). Use an approved production test identity.

## Release decision

| Gate | Status |
|------|--------|
| Code merged to `master` | **Done** — `ecc8d51` |
| CI green | **Done** — run 40076839905 |
| Preview + AUTH evidence | **Done** |
| Railway production deploy | **Blocked** — needs Railway authentication / manual redeploy |
| Live smoke | **Pending** deploy |
