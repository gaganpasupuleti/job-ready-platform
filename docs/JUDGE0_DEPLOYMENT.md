# Judge0 Production Deployment (Build 4.2)

This document covers hosting **Judge0 CE** as an isolated execution plane for Job Ready Platform coding practice.

## 1. Why not Railway for the worker?

Official Judge0 CE uses **privileged containers** and Linux **isolate** for sandboxing. Typical PaaS app containers (including Railway) do not provide the required cgroup/isolate capabilities.

**Preferred:** small dedicated Linux VPS/VM with Docker Compose (`infra/judge0/`).

**Alternative:** any Judge0-compatible HTTP API. Job Ready only needs `JUDGE0_URL` + auth configuration.

## 2. Version pin

| Item | Value |
|------|-------|
| Image | `judge0/judge0:1.13.1` |
| Selected / tested | 2026-08-29 |
| Compose path | `infra/judge0/docker-compose.yml` |

Never deploy `judge0/judge0:latest` for production without pinning and re-testing.

Upgrade is a **Judge0-only** change — not tied to Job Ready app releases. See `infra/judge0/README.md`.

## 3. Architecture

```
Browser  →  Railway Frontend
               ↓
         Railway FastAPI  ──private/authenticated HTTPS──►  Judge0 Server :2358
                                                               ↓
                                                         Judge0 Worker (isolate)
                                                               ↓
                                              Judge0 Postgres + Judge0 Redis
```

Isolated from:

- Job Ready application Postgres
- Job Ready Redis
- SQL practice sandbox Postgres

## 4. Ubuntu VPS checklist

1. Provision Ubuntu 22.04+ (2 vCPU / 4 GB RAM minimum recommended).
2. Install Docker Engine + Compose plugin.
3. Clone this repo (or copy `infra/judge0/`).
4. Copy `.env.example` → `.env` and `judge0.conf.example` → `judge0.conf`.
5. Generate strong secrets (`openssl rand -hex 32`) for Postgres, Redis, and `AUTHN_TOKEN`.
6. Align `AUTHN_TOKEN` in `judge0.conf` with Railway `JUDGE0_AUTH_TOKEN`.
7. `docker compose up -d`
8. Firewall: allow `:2358` only from backend egress IPs (or VPN).
9. Optional: Caddy/Nginx TLS reverse proxy if the API must be on the public internet.
10. Point Railway backend env at the Judge0 URL and enable `JUDGE0_ENABLED=true`.

## 5. Backend configuration

See root `.env.example` for the full list. Critical keys:

```
JUDGE0_ENABLED=true
JUDGE0_URL=
JUDGE0_AUTH_HEADER=X-Auth-Token
JUDGE0_AUTH_TOKEN=
JUDGE0_TIMEOUT_SECONDS=30
JUDGE0_POLL_INTERVAL_MS=500
JUDGE0_MAX_POLL_SECONDS=45
JUDGE0_MAX_CPU_TIME_SECONDS=15
JUDGE0_MAX_WALL_TIME_SECONDS=20
JUDGE0_MAX_MEMORY_KB=256000
CODING_MAX_SOURCE_CHARS=65536
CODING_MAX_STDIN_CHARS=100000
CODING_RUNS_PER_MINUTE=20
CODING_SUBMITS_PER_MINUTE=10
CODING_MAX_CONCURRENT_EXECUTIONS_PER_USER=2
```

## 6. Language IDs (Judge0 CE defaults)

| Key | Judge0 ID | Typical label |
|-----|-----------|---------------|
| python | 71 | Python 3.x |
| java | 62 | Java (OpenJDK) |
| cpp | 54 | C++ (GCC) |
| javascript | 63 | JavaScript (Node.js) |

At startup the backend queries `GET /languages` and refreshes display names / availability. The backend rejects unknown language IDs from the client.

## 7. Smoke tests (production)

After wiring:

1. `GET /api/v1/coding/execution-status` → `available: true`
2. Run/Submit Python, Java, C++, JavaScript Accepted solutions
3. Wrong Answer / Compilation Error / Runtime Error / TLE
4. Stop Judge0 → UI shows “Code execution is currently unavailable.” Auth/MCQ/SQL still work

## 8. Live integration tests (optional)

```bash
cd backend
set JUDGE0_LIVE_TESTS=1
set JUDGE0_URL=http://localhost:2358
set JUDGE0_AUTH_TOKEN=...
pytest tests/test_judge0_live.py -q
```

These are **disabled by default** and must not run in normal CI.

## 9. Security expectations

- No `subprocess` / `exec` / `eval` of student code in FastAPI
- Auth token never sent to the frontend
- Hidden test I/O never returned on Submit
- Compiler/runtime messages sanitized (paths, hosts, tokens)
- Rate limits + per-user concurrency via Redis (Job Ready Redis — coordination only, not Judge0 Redis)
