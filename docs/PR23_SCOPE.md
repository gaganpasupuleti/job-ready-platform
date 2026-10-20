# PR #23 scope reconciliation

## What reviewers see

`feat/official-roadmaps-retro-ui` vs `master` includes **Power BI lab/report work** from commits that predate the roadmap audit delivery:

| Commit | Summary |
|--------|---------|
| `6feebb7` | Power BI preview and student build lab |
| `e12b145` | Power BI workshop baselines and packaging |
| `24ea439` | Official roadmaps viewer + retro shell (start of roadmap UI track) |
| `962e657` … `b0dbff1` | Audit delivery (reliability, Jobs, docs) |
| *(after audit)* | Corrective pass commits on same branch |

Power BI changes are **inherited branch history**, not introduced by the roadmap audit commits alone. They were **not removed** per product request to preserve unrelated WIP.

## How to review roadmap/UI only

1. **Diff range (roadmap audit only):** `24ea439^..HEAD` filtered to `roadmap*`, `official-roadmap`, `JobsHubPage`, `jobready-retro.css`, `PageIntro`, `FilterDisclosure`, `roadmap.py`, `official_roadmap_service.py`, and related tests/docs.
2. **Or compare commits:** `962e657` (first reliability commit) through latest corrective commit on this branch.
3. **Optional isolated branch (no force-push):** `git checkout -b feat/roadmap-ui-only master` then cherry-pick roadmap commits; resolve conflicts with Power BI files if needed.

## Dependencies

Roadmap UI commits do **not** require Power BI runtime for verification. Power BI routes/assets are orthogonal unless merging the full branch to `master`.
