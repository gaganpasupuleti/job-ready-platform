# Visual Learning Phase 1 release

PR #17 adds the diagram renderer and the six static files. Merging it does not publish lesson text. Production students see the diagrams only after the frontend deploy and the one-time import below.

Do not change Railway variables. Do not point `scripts/content_batch.py` at production. That command still accepts only `--target local`.

## 1. Merge

Merge PR #17 after a human review of `c32ef0027a72828635cadec0b924753d2a5b0227` or a later commit on `feature/visual-learning-phase1`. CI must be green. This document does not authorize the merge.

## 2. Deploy the frontend only

The frontend image builds `frontend/Dockerfile` (the same `serve -s dist` command as `infra/docker/Dockerfile.frontend`). Vite copies `frontend/public/learning-visuals/` into the site root.

Redeploy the existing frontend service from the merged commit. Keep the current build arguments:

- `VITE_API_BASE_URL` stays the current public API origin
- `VITE_ENABLE_DEV_LOGIN=false`
- `VITE_GOOGLE_CLIENT_ID` stays as it is

A backend deploy is not required to render lesson Markdown. The running API already returns `body_md`. The import in step 4 runs from a trusted checkout of this commit. It does not need to be inside the backend image.

## 3. Check the six assets

From `frontend`, after the frontend deployment:

```text
ASSET_BASE_URL=https://frontend-production-f65c0.up.railway.app node --experimental-strip-types scripts/check-learning-visual-assets.ts
```

Each of these paths must return HTTP 200, an SVG content type, and pass the static SVG allowlist:

- `/learning-visuals/crt/percentages-quarter.svg`
- `/learning-visuals/crt/number-pattern.svg`
- `/learning-visuals/crt/verbal-claim.svg`
- `/learning-visuals/crt/data-interpretation.svg`
- `/learning-visuals/dsa/complexity-growth.svg`
- `/learning-visuals/dsa/array-reversal.svg`

Without `ASSET_BASE_URL`, the same script checks only the local files.

## 4. Back up, plan, then import

Take a custom-format dump of the application Postgres service named `Postgres`, database `railway`, before the import. Store it outside git. Do not dump the Jobs server.

Then, from `backend` on this commit, with `DATABASE_URL` set to the application database and not printed:

```text
python scripts/visual_phase1_release.py plan
```

The plan must show six updates, database fingerprint `HOST:PORT/railway`, and no rejections. It writes nothing.

Publish only if that plan is right:

```text
$env:VISUAL_PHASE1_AUTHORIZATION = "PUBLISH-2026-10-10-VISUAL-LEARNING-001"
python scripts/visual_phase1_release.py apply --confirm-database HOST:PORT/railway --confirm-keys crt-di-tables,crt-logical-patterns,crt-quant-percentages,crt-verbal-meaning,dsa-arrays-strings,dsa-complexity --backup-out PATH-OUTSIDE-GIT.json
```

The authorization value, the database fingerprint, and the six keys are all required. The command refuses a missing lesson, a lesson that is not the published version 1 snapshot, a partial publication, or any syllabus or question change. A second apply is idempotent.

## 5. Student acceptance

Sign in as an authorized student on desktop and mobile. Open:

- `/learn/syllabus/syl-crt-quant-percentages`
- `/learn/syllabus/syl-crt-logical-patterns`
- `/learn/syllabus/syl-crt-verbal-meaning`
- `/learn/syllabus/syl-crt-di-tables`
- `/learn/syllabus/syl-dsa-complexity`
- `/learn/syllabus/syl-dsa-arrays-strings`

Each page shows its diagram and caption, the worked example, and the existing practice question. Mark one lesson read and confirm the same material stays read.

`frontend/e2e/learning-visuals-acceptance-responsive.spec.ts` is the local signed-in rehearsal of those six pages. It does not call production.

## Rollback

If the diagrams should be removed, restore the pre-import lesson rows from the backup file. This does not restore the database from the full dump and does not touch reading progress:

```text
$env:VISUAL_PHASE1_AUTHORIZATION = "ROLLBACK-2026-10-10-VISUAL-LEARNING-001"
python scripts/visual_phase1_release.py rollback --confirm-database HOST:PORT/railway --confirm-keys crt-di-tables,crt-logical-patterns,crt-quant-percentages,crt-verbal-meaning,dsa-arrays-strings,dsa-complexity --backup-in PATH-OUTSIDE-GIT.json
```

Rollback refuses if the lesson id changed or the row is no longer the published version 2 body. If the row-level rollback is not enough, restore the full Postgres dump into a new database and repoint the backend. Do not drop the live database first.

To roll back a bad frontend deploy, redeploy the previous frontend deployment. Lesson text can stay at version 2; missing image files show “Diagram unavailable” plus the alt text.
