# Judge0 CE (Build 4.2) — reference wrapper

**Production path:** use the **official** Judge0 CE **v1.13.1** zip on Ubuntu 22.04  
(see [docs/JUDGE0_DEPLOYMENT.md](../../docs/JUDGE0_DEPLOYMENT.md) — cgroup grub + official compose order).

This directory pins the same image tag for reference / alternate compose.

| Field | Value |
|-------|-------|
| Image | `judge0/judge0:1.13.1` |
| Official zip | `https://github.com/judge0/judge0/releases/download/v1.13.1/judge0-v1.13.1.zip` |
| Date selected | 2026-08-29 |

## Topology

```
server (API :2358) ──► redis (Judge0-only)
       │
workers (isolate) ──► postgres (Judge0-only)
```

Do **not** reuse Job Ready Railway Postgres, Redis, or the SQL practice sandbox.

## Requirements

- Linux VPS with Docker Engine + Compose v2
- Privileged containers
- Ubuntu 22.04 + `systemd.unified_cgroup_hierarchy=0` (Judge0 1.13.1 docs)

## Official quick path (preferred)

```bash
wget https://github.com/judge0/judge0/releases/download/v1.13.1/judge0-v1.13.1.zip
unzip judge0-v1.13.1.zip && cd judge0-v1.13.1
# edit judge0.conf: POSTGRES_PASSWORD, REDIS_PASSWORD, AUTHN_TOKEN
docker compose up -d db redis && sleep 10 && docker compose up -d
```

## This wrapper (optional)

```bash
cd infra/judge0
cp .env.example .env
cp judge0.conf.example judge0.conf
# fill secrets — keep AUTHN_TOKEN identical to Railway JUDGE0_AUTH_TOKEN
docker compose up -d db redis
sleep 10
docker compose up -d
```

## HTTPS + Railway

Put TLS in front of `:2358`. Then:

```
JUDGE0_ENABLED=true
JUDGE0_URL=https://judge.example.com
JUDGE0_AUTH_HEADER=X-Auth-Token
JUDGE0_AUTH_TOKEN=<same as AUTHN_TOKEN>
```

Never expose the token to the frontend. Verification: [docs/JUDGE0_VERIFICATION.md](../../docs/JUDGE0_VERIFICATION.md).
