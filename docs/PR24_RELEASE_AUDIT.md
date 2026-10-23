# PR #24 release audit — roadmap / UI only

**Branch:** `feat/roadmap-ui-clean`  
**PR:** https://github.com/gaganpasupuleti/job-ready-platform/pull/24  
**Candidate SHA (code):** `fe03c7c`  
**Docs tip:** `9dd2178`  
**CI (latest):** https://github.com/gaganpasupuleti/job-ready-platform/actions/runs/40021707444  
**Status:** Open — not merged, not deployed.

## Root causes and fixes (`252196d` → `fe03c7c`)

| Issue | Root cause | Fix |
|-------|------------|-----|
| Cache integrity loss | v1 cache stored normalized graph only; read path re-validated filtered edges → `classification=clean` | **Cache v2 envelope**: `source_payload`, `served`, `integrity`; recompute on read; delete legacy flat files |
| Six “failed” upstream maps | Zero-edge map treated invalid; duplicate edge IDs failed strict validation | **`edgeless`** classification; deterministic **`duplicate_id_remapped`** (`__jobready-dupN`); identical dupes dropped |
| Catalog E2E false fail | Assert required `removed_edges` for every `sanitized` slug | Accept **`edge_normalizations` or `removed_edges`** as evidence |
| CI acceptance-shots | `getByText(/CRT)` matched heading + body (strict mode) | Locator: `getByRole('heading', { name: /CRT \/ Aptitude/i, level: 2 })` |
| Validation parity | Frontend/audit allowed whitespace IDs on served graphs | `isNonEmptyId` in `graphValidation.ts` + `roadmapGraphAudit.mjs` |

**Commits:** `9d3b2a9` (cache + normalization), `c7b7c48` (frontend parity), `fe03c7c` (catalog totals).

## Graph integrity contract

API field `integrity` on `GET /api/v1/roadmap/official/{slug}/graph`:

| `classification` | Meaning |
|------------------|---------|
| `clean` | No normalization applied |
| `edgeless` | Valid nodes, zero edges (e.g. `code-review`) |
| `sanitized` | Deterministic normalization (`edge_normalizations`, `removed_edges`) |

**Cache v2 envelope** stores `source_payload` (raw upstream), `served` graph, and `integrity`.  
Cache reads **recompute** integrity from `source_payload` and reject stale/legacy files (no re-classifying sanitized graphs as `clean`).

E2E catalog statuses: `clean` | `edgeless` | `sanitized` | `fail` | `unavailable`.  
**Mounted** = clean + edgeless + sanitized (93 target). **Upstream-clean only** = `clean` count (85).

## Upstream audit (`docs/roadmap-upstream-graph-integrity.json`)

Latest local run (`audit_upstream_graph_integrity.py`, parity with API normalization):

| Outcome | Count | Slugs |
|---------|------:|-------|
| clean | 85 | _(see JSON)_ |
| edgeless | 1 | `code-review` |
| sanitized | 7 | see table below |
| failed | 0 | — |
| unavailable | 0 | — |
| **Total** | **93** | all bundled catalog slugs recorded |

### Former “rejected” maps (now mounted with classification)

| Slug | Was | Now | Decision |
|------|-----|-----|----------|
| `code-review` | fail (0 edges) | **edgeless** | 18 independent nodes; no invented edges |
| `design-system`, `django`, `javascript`, `mongodb` | fail (dup IDs) | **sanitized** | Conflicting records under same ID → second+ remapped deterministically |
| `golang` | fail (2 dup IDs) | **sanitized** | Two collision groups remapped |

### Dangling-edge maps (sanitized, semantic path unresolved)

| Slug | Removed edge | Impact |
|------|--------------|--------|
| `data-analyst` | `xy-edge__aopqiF0Svmpq94g6OQBX0x2-9sIP-jpNjtA1JPCBjTf-Hz2` — source node `aopqiF0Svmpq94g6OQBX0` missing | Target topic keeps other edges; **learning path through removed link not verified** |
| `ux-design` | dangling source `dgBELpFRvRO_7ir0y0AtX` | Same — **unresolved**; do not add replacement edges |

## Focused test results (local, `fe03c7c`)

| Suite | Result |
|-------|--------|
| `pytest` `test_roadmap_official.py` + `test_roadmap_graph_cache.py` | **11 passed** |
| Frontend `npm run test:unit` | **38 passed** (incl. edgeless, whitespace ID, duplicate-edge audit cases) |
| `audit_upstream_graph_integrity.py` | **93/93** fetched; 0 failed |

Cache regression coverage: roundtrip preserves `sanitized` counts/`removed_edges`; repeated reads stable; legacy cache deleted.

## CI history

| Run | SHA | Result | Notes |
|-----|-----|--------|-------|
| [39998583379](https://github.com/gaganpasupuleti/job-ready-platform/actions/runs/39998583379) | `252196d` | **fail** | See below |
| [40021707444](https://github.com/gaganpasupuleti/job-ready-platform/actions/runs/40021707444) | `9dd2178` | **in progress** | Full CI on integrity + catalog evidence fix |
| [40021446428](https://github.com/gaganpasupuleti/job-ready-platform/actions/runs/40021446428) | `fe03c7c` | cancelled | Superseded (concurrency) |

### Run 39998583379 (investigation)

- **Playwright desktop:** ~142 passed, **2 failed** (job-level).
- **`acceptance-shots`:** strict-mode violation — multiple elements matched CRT/Aptitude text (fixed in `acceptance-shots.spec.ts`).
- **`roadmap-catalog-render`:** 6 slugs **unavailable** (graph HTTP 502 after retries); `mongodb` **fail** (socket hang up). Upstream fetch pressure / pre-normalization failures — not assertion timeouts.
- **Graph interaction specs:** passed on that run (drag edge, lock/reset, viewport).

**CI pass/fail on `fe03c7c`:** _fill when run 40021446428 completes._

## Article audit, preview smoke, visual

| Check | Environment | Status |
|-------|-------------|--------|
| Authenticated catalog graph audit (`audit-roadmap-catalog.mjs`) | Local | **Not run** — requires live API + bearer token (same as CI E2E seed) |
| Article content sampling | — | **Not run** this session; prior PR evidence separate from `fe03c7c` |
| Production-preview smoke | Hosted preview + compatible API | **Blocked** — no production deploy; preview must target backend with cache v2 |
| Visual/contrast (`ui-cohesion` / contrast report) | Local screenshots in `e2e/artifacts/` (WIP, uncommitted) | **Partial** — manual contrast pass not re-signed on `fe03c7c` |

Keep **mocked**, **CI-backend**, and **hosted-production** evidence separate in release sign-off.

## Remaining release blockers

1. **Green CI** on `fe03c7c` (full Playwright desktop, all 93 catalog slugs).
2. **Manual sign-off** on **7 sanitized + 1 edgeless** (especially **data-analyst** / **ux-design** semantic paths).
3. **Authenticated graph + article audit** against CI-equivalent backend on final SHA.
4. **Production-preview smoke** once preview URL points at compatible API.
5. **Visual/contrast** sign-off where transparency limits allow.

Do not merge or deploy until blockers are cleared.
