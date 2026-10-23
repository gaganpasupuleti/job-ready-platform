# PR #24 release audit — roadmap / UI only

**Branch:** `feat/roadmap-ui-clean`  
**PR:** https://github.com/gaganpasupuleti/job-ready-platform/pull/24  
**Release candidate SHA:** `3556a7d` (green CI); follow-up test commit pending push  
**Green CI:** https://github.com/gaganpasupuleti/job-ready-platform/actions/runs/40022619114  
**Status:** Open — not merged, not deployed.

---

## Steps 1–6 completion (release engineering)

### 1. Cache integrity (done)

- **Cache v2** (`cache_version: 2`): `source_payload`, `served`, `integrity`, `source`, `source_payload_sha256`, `fetched_at`.
- **Read path:** `graph_response_from_cache_envelope()` recomputes from `source_payload`; mismatch → cache miss / refetch.
- **Legacy:** flat v1 files deleted on read.
- **Tests:** `test_roadmap_graph_cache.py` — sanitized roundtrip, repeated read, legacy invalidation, **malformed envelope rejected**.

### 2. Validation parity (done)

| Layer | Strict on upstream fetch | On served API graph |
|-------|--------------------------|---------------------|
| Backend `roadmap_graph_normalization.py` | whitespace IDs, dup node IDs, bool/NaN/inf coords, dup edge IDs (pre-remap), dangling drop | N/A (already normalized) |
| Frontend `graphValidation.ts` | — | non-empty IDs, finite coords, unique IDs, valid endpoints |
| CLI `roadmapGraphAudit.mjs` | — | same as frontend + handle rules |
| E2E `roadmap-catalog-shared.ts` | — | integrity contract + sanitized evidence |

**Tests:** backend `test_roadmap_official.py` (edgeless, dangling, dup remap, bool/whitespace coords, order permutations); frontend unit (edgeless, whitespace, dup edges).

### 3. Six formerly rejected maps (done)

| Slug | Upstream issue | Classification | Connections preserved |
|------|----------------|----------------|----------------------|
| `code-review` | 18 nodes, 0 edges | **edgeless** | N/A — intentional node-only layout |
| `design-system` | 1 duplicate edge ID, distinct endpoints | **sanitized** | Both edges kept; second ID `…__jobready-dup1` |
| `django` | duplicate edge ID | **sanitized** | remapped |
| `javascript` | duplicate edge ID | **sanitized** | remapped |
| `golang` | 2 duplicate edge ID groups | **sanitized** | 2 remaps; 77/77 edges retained |
| `mongodb` | duplicate edge ID | **sanitized** | remapped |

Duplicate records were **not** identical — conflicting endpoints under the same ID. No silent drops except exact duplicate signatures.

### 4. Dangling-edge maps (done — semantic review)

| Slug | Removed | Render (CI E2E) | Learning path |
|------|---------|-----------------|---------------|
| `data-analyst` | 1 edge; missing source `aopqiF0Svmpq94g6OQBX0` → target `9sIP-jpNjtA1JPCBjTf-H` | **Mounts**; 40→browser nodes (viewport subset) | **Unresolved** — removed link was layout connector; alternate path **not** proven |
| `ux-design` | 1 edge; missing source `dgBELpFRvRO_7ir0y0AtX` → target `0vLaVNJaJSHZ_bHli6Qzs` | **Mounts** | **Unresolved** — no replacement edge added |

### 5. Audit consistency (done)

**Single contract:** `integrity.classification` ∈ `clean` | `edgeless` | `sanitized` | (failure = HTTP/validation error).

| Channel | Artifact / behavior |
|---------|---------------------|
| Upstream CLI | `docs/roadmap-upstream-graph-integrity.json` — **93 rows**, no early exit |
| API | `integrity` on graph response; cache hit recomputes from `source_payload` |
| E2E catalog | `docs/ci-evidence/roadmap-catalog-browser-40022619114.json` |
| Warm cache | logs clean / edgeless / sanitized counts |

**Catalog totals (upstream CLI + CI browser, aligned):**

| clean | edgeless | sanitized | fail | unavailable |
|------:|---------:|----------:|-----:|------------:|
| 85 | 1 (`code-review`) | 7 | 0 | 0 |
| **93** | | | | |

**Sanitized slugs (not upstream-clean):** `data-analyst`, `design-system`, `django`, `golang`, `javascript`, `mongodb`, `ux-design`.

### 6. CI investigation (done)

| Run | SHA | Result | Notes |
|-----|-----|--------|-------|
| [39998583379](https://github.com/gaganpasupuleti/job-ready-platform/actions/runs/39998583379) | `252196d` | **fail** | acceptance-shots strict mode; catalog 6×502 + mongodb hang; **pre** cache v2 / normalization |
| [40022619114](https://github.com/gaganpasupuleti/job-ready-platform/actions/runs/40022619114) | `3556a7d` | **success** | See below |

**40022619114 evidence:**

| Job | Result |
|-----|--------|
| Frontend lint, unit, build | pass |
| Backend pytest | **345 passed**, 10 skipped |
| Playwright desktop | **145 passed**, 6 skipped, 0 failed, 0 flaky (20.2m) |

**Roadmap-specific Playwright (all pass on green run):**

- `roadmap-catalog-render` — 93/93 mounted (85 clean + 1 edgeless + 7 sanitized)
- `roadmap-graph-interaction` — drag connected edge, lock/unlock/reset, viewport across panels
- `acceptance-shots` — CRT/Aptitude heading locator fix

Graph interaction and viewport checks were **not** weakened (no timeout inflation or error suppression for green).

---

## Focused regression tests (local)

| Suite | Result |
|-------|--------|
| `test_roadmap_official.py` + `test_roadmap_graph_cache.py` | 12+ passed (incl. malformed cache envelope, whitespace ID) |
| Frontend `npm run test:unit` | 38 passed |

---

## Remaining release blockers (steps 7–8 / sign-off)

1. **Push** final test/evidence commit (malformed-cache + whitespace parity + `docs/ci-evidence/`).
2. **Manual product sign-off** on 8 non–upstream-clean maps (especially dangling-edge semantics).
3. **Article audit** — sampled content checks with explicit uncovered slugs (not re-run on `3556a7d` in this pass).
4. **Production-preview smoke** — blocked until preview uses API with cache v2 on candidate SHA.
5. **Visual/contrast** — not re-certified on green SHA (local WIP screenshots uncommitted).

Do not merge or deploy until blockers 2–5 are accepted for release.
