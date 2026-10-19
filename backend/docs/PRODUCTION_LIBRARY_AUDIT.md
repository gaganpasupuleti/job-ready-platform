# Library — production readiness audit (2026-10-19)

## Catalog cleanup (done on local/dev database)

| Step | Result |
|------|--------|
| Removed **CODEQUEST OWNERSHIP AND LICENSE** | Deleted from `library_books` |
| Ran `scripts/library_dedupe_catalog.py` | **158 → 61** published rows (unique titles; dropped duplicate ingests + all `report` stubs) |
| Ingest hardening | `library_r2_ingest.py` skips `Book Reports`, `report.pdf`, Codequest license files |

Re-run after future bulk imports:

```powershell
cd backend
.\.venv\Scripts\python.exe scripts\library_dedupe_catalog.py --dry-run
.\.venv\Scripts\python.exe scripts\library_dedupe_catalog.py
```

**Production:** run the same dedupe script against **Railway Postgres** once after first prod ingest (or after migrating dev data).

## Backend tests (local)

- `tests/test_library.py` — pass
- `tests/test_library_reader.py` — pass
- `tests/test_library_storage.py` — pass

## Required for production deploy

### Backend (`feature/student-library` or merged `master`)

- Library routes: `/api/v1/library/*`, admin `/api/v1/admin/library/*`
- **R2 env** (private bucket): `LIBRARY_R2_ACCOUNT_ID`, `LIBRARY_R2_BUCKET`, `LIBRARY_R2_ACCESS_KEY_ID`, `LIBRARY_R2_SECRET_ACCESS_KEY`
- PDFs served via **API proxy** (`/books/{id}/file`) — R2 `read_bytes` enabled (no browser CORS required)
- Migrations applied for `library_books`, bookmarks, reading status tables

### Frontend (integration worktree `feat/jobready-quiz-library-frontend`)

- Routes: `/library`, `/library/:id`, `/library/:id/read`, `/admin/library`
- **More → Career → Library**; reader **Full screen** control
- Merge integration branch into deploy branch before Railway frontend build

### Not on prod today (verify after deploy)

- Prod `master` (~Oct 2026) had **no** student library UI; deploy must include **both** backend library module and frontend integration patch.

### Post-deploy smoke

1. Login as student → **More → Library** → count shows **61** published (after prod dedupe).
2. Open any book → **Read PDF** → pages render; **Full screen** works.
3. Admin email/password login → **More → Library** (admin) for catalog ops; bulk ingest remains **CLI** (`library_r2_ingest.py`), not required for students.

### Secrets / ops

- Do not commit `.env` or R2 keys.
- Orphan objects may remain in R2 for deleted catalog rows; optional bucket cleanup later.

## Deploy order (recommended)

1. Deploy **backend** with library + R2 config.
2. `library_r2_ingest.py sync` (if objects already in R2) or migrate catalog from dev.
3. `library_dedupe_catalog.py` on **production DB**.
4. Deploy **frontend** with library pages.
5. Smoke test read + fullscreen.
