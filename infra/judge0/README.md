# Judge0 CE (Build 4.2)

Pinned production image: **`judge0/judge0:1.13.1`**

| Field | Value |
|-------|-------|
| Image | `judge0/judge0:1.13.1` |
| Date selected | 2026-08-29 |
| Flavor | Judge0 CE (Community Edition) |
| Lifecycle | Independent of Job Ready app deploys |

## Topology

```
server (API :2358) ──► redis (Judge0-only)
       │
worker (isolate)  ──► postgres (Judge0-only)
```

Do **not** reuse Job Ready Railway Postgres, Redis, or the SQL practice sandbox.

## Requirements

- Linux VPS/VM with Docker Engine + Docker Compose v2
- Privileged containers (`privileged: true`) for isolate/cgroup
- Outbound network for language packages only as needed by the image
- **Not supported on typical Railway app containers** (no privileged isolate)

Compatible hosts conceptually: Ubuntu VPS, EC2, DigitalOcean Droplet, Hetzner Cloud, any Linux provider allowing privileged Docker.

## Quick start

```bash
cd infra/judge0
cp .env.example .env
cp judge0.conf.example judge0.conf

# Generate secrets
openssl rand -hex 24   # → JUDGE0_POSTGRES_PASSWORD + POSTGRES_PASSWORD in conf
openssl rand -hex 24   # → JUDGE0_REDIS_PASSWORD + REDIS_PASSWORD in conf
openssl rand -hex 32   # → JUDGE0_AUTH_TOKEN + AUTHN_TOKEN in conf

# Keep AUTHN_TOKEN in judge0.conf identical to JUDGE0_AUTH_TOKEN used by FastAPI
docker compose up -d
```

Wait ~30–60s for workers, then:

```bash
curl -s -H "X-Auth-Token: $JUDGE0_AUTH_TOKEN" http://127.0.0.1:2358/about
curl -s -H "X-Auth-Token: $JUDGE0_AUTH_TOKEN" http://127.0.0.1:2358/languages | head
```

## Firewall

- Prefer **private network / VPN / firewall allowlist** so only the Railway backend (or your API IP) can reach `:2358`.
- If public HTTPS is required: put Nginx/Caddy TLS in front; never send `X-Auth-Token` over plaintext internet.
- Do not expose Judge0 Postgres (5432) or Redis publicly.

## Job Ready backend env (Railway)

```
JUDGE0_ENABLED=true
JUDGE0_URL=https://judge.example.com   # or http://private-ip:2358
JUDGE0_AUTH_HEADER=X-Auth-Token
JUDGE0_AUTH_TOKEN=<same as AUTHN_TOKEN>
JUDGE0_TIMEOUT_SECONDS=30
JUDGE0_POLL_INTERVAL_MS=500
JUDGE0_MAX_POLL_SECONDS=45
```

Frontend never receives Judge0 credentials.

## Upgrade procedure

1. Read Judge0 CE release notes for the target tag.
2. Snapshot/backup `judge0_postgres_data` volume.
3. Change image tag in `docker-compose.yml` (both server and worker).
4. `docker compose pull && docker compose up -d`
5. Smoke-test languages + Python submission from Job Ready.
6. Do **not** auto-upgrade when deploying Job Ready app code.

## Backup

- Postgres volume: `docker run --rm -v infra_judge0_judge0_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/judge0-pg.tgz /data`
- Redis AOF is secondary; submissions are ephemeral for Job Ready (results stored in Job Ready DB).

## Health verification

```bash
curl -fsS -H "X-Auth-Token: $JUDGE0_AUTH_TOKEN" "$JUDGE0_URL/about"
curl -fsS -H "X-Auth-Token: $JUDGE0_AUTH_TOKEN" "$JUDGE0_URL/languages"
```

From Job Ready: `GET /api/v1/coding/execution-status` → `available: true`, `provider: judge0`.

## Security notes

- Student code never runs in FastAPI / Railway backend.
- Separate Postgres + Redis passwords from Job Ready.
- Auth token only on backend → Judge0.
- Live isolation tests: student code must not see Job Ready env, DB URLs, or SQL sandbox.

## Option B — external Judge0-compatible API

If you use a hosted Judge0-compatible service, set `JUDGE0_URL` + auth header/token only. No VPS compose required. Still pin and document the provider version when possible.
