# Railway deployment notes (Build 7.2)

Do **not** apply destructive production changes from this doc without an explicit ops decision.

## Frontend

- Image uses `serve -s dist` (`infra/docker/Dockerfile.frontend`) — SPA fallback is enabled so deep links like `/practice/sql/:slug` survive refresh.
- Build args:
  - `VITE_API_BASE_URL` — public API origin (required for browser calls)
  - `VITE_ENABLE_DEV_LOGIN=false` — **must** be false/absent in production so admin credentials are not pre-filled

## Backend

Required:

- `DATABASE_URL`
- `JWT_SECRET_KEY` — production refuses the default insecure value when `APP_ENV=production`
- `CORS_ORIGINS` / `cors_origins` including the frontend origin

Recommended:

- `REDIS_URL` (optional; app degrades without Redis)
- `SQL_EXECUTION_ENABLED=true` with sandbox URLs when SQL practice is on
- `SQL_SANDBOX_ADMIN_DATABASE_URL`
- `SQL_SANDBOX_RUNNER_DATABASE_URL` (or derived runner password/role)
- `JUDGE0_ENABLED=false` until a privileged Judge0 VM exists (see `docs/JUDGE0_DEPLOYMENT.md`)

## Health

`GET /api/v1/health` returns coarse checks (`database`, `redis`, `sql_sandbox`, `judge0`) without DSNs or passwords.

`GET /api/v1/sql/execution-status` remains the student-facing SQL availability signal.

## Smoke

```bash
python scripts/smoke.py --base-url https://<your-api-host>
```

## Security headers

API sets lightweight `X-Content-Type-Options`, `Referrer-Policy`, and `X-Frame-Options`. CSP is deferred (Monaco / CDN risk).

## Auth token note

Access tokens remain in `localStorage` for Build 7.2. Future consideration: HttpOnly secure cookies. Logout and 401 handling clear the token and send users to `/login` without looping auth endpoints.
