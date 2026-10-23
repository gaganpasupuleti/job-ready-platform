# PR #24 release audit — roadmap / UI only

**Branch:** `feat/roadmap-ui-clean`  
**PR:** https://github.com/gaganpasupuleti/job-ready-platform/pull/24  
**Candidate SHA:** _(set after push)_  
**Status:** Open — not merged, not deployed.

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
**Mounted** = clean + edgeless + sanitized (93 target). **Upstream-clean only** = `clean` count.

## Upstream audit (`docs/roadmap-upstream-graph-integrity.json`)

Latest local run (normalization parity with API):

| Total | Count |
|-------|------:|
| clean | 85 |
| edgeless | 1 (`code-review`) |
| sanitized | 7 |
| failed | 0 |
| unavailable | 0 |

### Sanitized maps (require manual review — not upstream-clean)

| Slug | Normalization | Semantic path |
|------|---------------|-----------------|
| `data-analyst` | 1 dangling edge removed | **Unresolved** — missing source node `aopqiF0Svmpq94g6OQBX0`; target `9sIP-jpNjtA1JPCBjTf-H` remains without that incoming link |
| `ux-design` | 1 dangling edge removed | **Unresolved** — missing source `dgBELpFRvRO_7ir0y0AtX` |
| `design-system` | duplicate edge ID remapped | Distinct connections shared ID `xy-edge__JfXwzkN29UGz17FYHHE3Az2-…` |
| `django` | duplicate edge ID remapped | Distinct endpoints under same ID |
| `javascript` | duplicate edge ID remapped | Distinct endpoints under same ID |
| `golang` | 2 duplicate IDs remapped | Two ID collision groups |
| `mongodb` | duplicate edge ID remapped | Distinct endpoints under same ID |

### Edgeless

| Slug | Notes |
|------|--------|
| `code-review` | 18 nodes, 0 edges — supported as intentional independent layout |

## CI

| Run | SHA | Result | Notes |
|-----|-----|--------|-------|
| [39998583379](https://github.com/gaganpasupuleti/job-ready-platform/actions/runs/39998583379) | `252196d` | fail | acceptance-shots strict mode; 6×502 graphs (pre-normalization); cache integrity loss |
| _next_ | _TBD_ | pending | Cache v2, duplicate remap, edgeless, acceptance fix |

**39998583379 Playwright:** ~142 passed; failures: syllabus acceptance shot; catalog (6 unavailable 502 + 1 fail socket hangup).

## Tests added

- `test_roadmap_graph_cache.py` — fetch → cache write → read preserves `sanitized` integrity; legacy cache invalidated
- `test_roadmap_official.py` — duplicate-ID remapping, edgeless, dangling, boolean coords rejected
- Normalization module: `roadmap_graph_normalization.py`

## Remaining release blockers

1. **Green CI** on final SHA (full Playwright desktop).
2. **Manual sign-off** on 7 sanitized + 1 edgeless maps (semantic path unresolved for 2 dangling-edge slugs).
3. **Authenticated catalog graph audit** + **preview smoke** on CI-equivalent backend.
4. **Contrast/screenshots** — unverified where `unsupported_transparency`.

Do not merge or deploy until blockers are cleared.
