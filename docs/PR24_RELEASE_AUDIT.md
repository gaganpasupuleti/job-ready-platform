# PR #24 release audit — roadmap / UI only

**Branch:** `feat/roadmap-ui-clean`  
**PR:** https://github.com/gaganpasupuleti/job-ready-platform/pull/24  
**Candidate SHA:** _(pending push — integrity contract + duplicate-ID fix)_  
**Status:** Open — not merged, not deployed.

## Graph integrity contract (`integrity` on `/roadmap/official/{slug}/graph`)

| `integrity.classification` | Meaning |
|----------------------------|---------|
| `clean` | Upstream nodes/edges valid; no edges removed |
| `sanitized` | Dangling upstream edges removed; see `removed_edges` |
| _(API 502)_ | Validation failed (duplicate edge IDs, zero edges after sanitize, malformed payload) |

E2E catalog reports **`clean` / `sanitized` / `fail` / `unavailable`** separately.  
**`clean` + `sanitized` = 93** means all maps **mount in browser**; only **`clean`** counts as upstream-valid.

## Upstream audit (`docs/roadmap-upstream-graph-integrity.json`)

Generated: `python -m scripts.audit_upstream_graph_integrity` (roadmap.sh `https://roadmap.sh/{slug}.json`).

| Totals (2026-10-23 local run) | Count |
|---------------------------------|------:|
| clean | 85 |
| sanitized | 2 |
| failed (validation) | 6 |
| unavailable (HTTP) | 0 |

### Sanitized (upstream dangling edge — not a normalization bug)

| Slug | Source | Nodes | Edges (orig → retained) | Removed edge | Missing endpoint | Learning-path note |
|------|--------|------:|-------------------------|--------------|------------------|---------------------|
| `data-analyst` | roadmap.sh/data-analyst.json | 156 | 41 → 40 | `xy-edge__aopqiF0Svmpq94g6OQBX0x2-…` | source `aopqiF0Svmpq94g6OQBX0` absent from nodes | Broken layout link only; target topic remains reachable via other edges. **Unresolved** whether removed source was a deleted spacer/topic. |
| `ux-design` | roadmap.sh/ux-design.json | 140 | 27 → 26 | `xy-edge__dgBELpFRvRO_7ir0y0AtXx2-…` | source `dgBELpFRvRO_7ir0y0AtX` absent | Same pattern as data-analyst. **Unresolved** semantic impact. |

### Failed validation (do not treat as sanitized passes)

| Slug | Issue | Evidence |
|------|-------|----------|
| `code-review` | **Zero edges**, 18 nodes | Upstream defect; API returns 502 |
| `design-system` | **Duplicate edge ID** in upstream | `duplicate_edge_ids`: `xy-edge__JfXwzkN29UGz17FYHHE3Az2-…` |
| `django` | Duplicate edge ID | same class |
| `golang` | Duplicate edge ID | same class |
| `javascript` | Duplicate edge ID | same class |
| `mongodb` | Duplicate edge ID | same class |

Duplicate-ID order dependency in sanitization is **fixed**: IDs checked across **all** input edges before dropping dangling edges (regression tests added).

## CI evidence

| Run | SHA | Playwright | Notes |
|-----|-----|------------|-------|
| [39918003098](https://github.com/gaganpasupuleti/job-ready-platform/actions/runs/39918003098) | `a50b08f` | 144 pass, 1 fail, 6 skip | 87 pass / 6×502 catalog; graph interaction green |
| _next_ | _TBD_ | _pending_ | Integrity + catalog clean/sanitized split; warm stagger |

## Remaining release blockers

1. **Green CI** — 6 upstream-invalid slugs still fail API validation (502); catalog cannot reach 93 mount until upstream fix or explicit product policy for edgeless/duplicate graphs.
2. **Sanitized maps** — `data-analyst`, `ux-design` need human sign-off on removed connections (unresolved semantics).
3. **Authenticated catalog audit** + **preview smoke** on CI-equivalent backend (local :8000 without E2E seed remains unverified).
4. **Contrast / screenshots** — `unsupported_transparency` = unverified.

Do not merge or deploy until blockers are cleared.
