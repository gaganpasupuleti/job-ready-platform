# Judge0 Production Deployment (Build 4.2)

Isolated execution plane for Job Ready coding practice. Checkpoint: commit `a903c1d`.

Student code must **never** run in FastAPI / Railway. Only Judge0 workers execute untrusted code.

---

## 1. Why a dedicated Linux VPS?

Judge0 CE uses **privileged** Docker containers and Linux **isolate**. Railway app containers cannot provide that. Host Judge0 alone on a small VM.

| Role | Where |
|------|--------|
| Frontend / FastAPI / app Postgres / Redis / SQL sandbox | Railway |
| Judge0 server + workers + Judge0 Postgres + Judge0 Redis | Dedicated Ubuntu VPS |

---

## 2. Version pin

| Item | Value |
|------|-------|
| Release | **Judge0 CE v1.13.1** |
| Image | `judge0/judge0:1.13.1` (via official release zip) |
| OS | **Ubuntu 22.04 LTS** (officially documented) |
| Selected | 2026-08-29 |

**Do not** deploy `judge0/judge0:latest` for production. Upgrade Judge0 on its own lifecycle — never auto-bump when Job Ready deploys.

Official artifact:

```text
https://github.com/judge0/judge0/releases/download/v1.13.1/judge0-v1.13.1.zip
```

---

## 3. VPS sizing

| Use | Spec |
|-----|------|
| **Initial students (recommended)** | **4 vCPU / 8 GB RAM / 50+ GB SSD** |
| Light smoke only | 2 vCPU / 4 GB RAM (Java/C++ + concurrency will feel tight) |

Providers (any Linux VPS with privileged Docker): Hetzner, DigitalOcean, EC2, generic Ubuntu cloud.

---

## 4. Architecture (production)

```
Browser → Railway Frontend
              ↓
        Railway FastAPI
              │
              │ HTTPS + X-Auth-Token
              ▼
     judge.yourdomain.com   (Caddy/Nginx TLS)
              │
              ▼
        Judge0 :2358  (localhost / private only)
              ├── workers (isolate, privileged)
              ├── Postgres (Judge0-only)
              └── Redis (Judge0-only)
```

**Do not** leave `http://VPS-IP:2358` as the final public production endpoint.

---

## 5. Ubuntu 22.04 — legacy cgroups (required for v1.13.1)

Judge0 v1.13.1 documents configuring **legacy cgroups** before deploy:

```bash
sudo nano /etc/default/grub
```

Set / extend:

```bash
GRUB_CMDLINE_LINUX="systemd.unified_cgroup_hierarchy=0"
```

Then:

```bash
sudo update-grub
sudo reboot
```

After reboot, confirm Docker works, then continue.

---

## 6. Install Docker + Compose

```bash
# Official Docker Engine install for Ubuntu, then:
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-v2
sudo usermod -aG docker "$USER"
# log out/in if needed
docker version
docker compose version
```

---

## 7. Official Judge0 1.13.1 deploy

```bash
cd /opt
sudo mkdir -p judge0 && sudo chown "$USER":"$USER" judge0
cd /opt/judge0

wget https://github.com/judge0/judge0/releases/download/v1.13.1/judge0-v1.13.1.zip
unzip judge0-v1.13.1.zip
cd judge0-v1.13.1
```

Edit `judge0.conf` — set **strong random** values at minimum:

```bash
POSTGRES_PASSWORD=$(openssl rand -hex 24)
REDIS_PASSWORD=$(openssl rand -hex 24)
# Also configure authentication (names may vary by conf template):
# AUTHN_HEADER=X-Auth-Token
# AUTHN_TOKEN=$(openssl rand -hex 32)
```

Save `AUTHN_TOKEN` somewhere safe — Railway `JUDGE0_AUTH_TOKEN` must match. **Never commit secrets.**

Start DB/Redis first, then the stack (official order):

```bash
docker compose up -d db redis
sleep 10
docker compose up -d
```

Default API port: **2358**.

Health:

```bash
curl -s -H "X-Auth-Token: $AUTHN_TOKEN" http://127.0.0.1:2358/about
curl -s -H "X-Auth-Token: $AUTHN_TOKEN" http://127.0.0.1:2358/languages | head
```

### Optional: repo wrapper

This repo also ships `infra/judge0/` (pinned `1.13.1` compose). Prefer the **official zip** for production parity with Judge0 release notes; keep `infra/judge0` as a thin reference.

---

## 8. HTTPS reverse proxy (before Railway)

Example with Caddy (TLS automatic):

```text
judge.yourdomain.com {
    reverse_proxy 127.0.0.1:2358
}
```

Firewall:

- Allow `443` (and `80` for ACME) from the internet **or** lock to known IPs.
- Do **not** publish `2358` publicly once the proxy is up.
- Never expose Judge0 Postgres/Redis ports.

---

## 9. Railway backend env

```
JUDGE0_ENABLED=true
JUDGE0_URL=https://judge.yourdomain.com
JUDGE0_AUTH_HEADER=X-Auth-Token
JUDGE0_AUTH_TOKEN=<same as AUTHN_TOKEN>
JUDGE0_TIMEOUT_SECONDS=30
JUDGE0_POLL_INTERVAL_MS=500
JUDGE0_MAX_POLL_SECONDS=45
```

Optional platform caps (already in `.env.example`):

```
JUDGE0_MAX_CPU_TIME_SECONDS=15
JUDGE0_MAX_WALL_TIME_SECONDS=20
JUDGE0_MAX_MEMORY_KB=256000
CODING_RUNS_PER_MINUTE=20
CODING_SUBMITS_PER_MINUTE=10
CODING_MAX_CONCURRENT_EXECUTIONS_PER_USER=2
```

**Never** put `JUDGE0_AUTH_TOKEN` in the frontend or `VITE_*` vars.

Redeploy the Railway **backend** after setting variables.

---

## 10. Verification before switching production

### A. Opt-in live suite (from a machine that can reach Judge0)

Windows PowerShell:

```powershell
cd backend
$env:JUDGE0_LIVE_TESTS = "1"
$env:JUDGE0_ENABLED = "true"
$env:JUDGE0_URL = "https://judge.yourdomain.com"
$env:JUDGE0_AUTH_HEADER = "X-Auth-Token"
$env:JUDGE0_AUTH_TOKEN = "<secret>"
python -m pytest tests/test_judge0_live.py -q --tb=short
```

Or use `scripts/verify_judge0_live.ps1` (see repo).

Expect:

| Language | Result |
|----------|--------|
| Python | ✅ |
| Java | ✅ |
| C++ | ✅ |
| JavaScript | ✅ |

Plus isolation check (`DATABASE_URL` / `JWT_SECRET_KEY` not visible in student env).

### B. Manual / product checks

| Check | Expect |
|-------|--------|
| Accepted | ✅ |
| Wrong Answer | ✅ |
| Compilation Error | ✅ |
| Runtime Error | ✅ |
| Time Limit Exceeded | ✅ |
| Public Run shows I/O | ✅ |
| Submit hides hidden I/O | ✅ |
| Judge0 stopped → `503` / unavailable UI | ✅ |
| Auth / MCQ / SQL still work during outage | ✅ |

### C. Production app

1. `GET /api/v1/coding/execution-status` → `enabled: true`, `available: true`, `provider: judge0`
2. Run/Submit from DSA workspace for all four languages

Checklist copy: [JUDGE0_VERIFICATION.md](JUDGE0_VERIFICATION.md)

---

## 11. Language IDs (Judge0 CE defaults)

| Key | ID | Typical label |
|-----|-----|----------------|
| python | 71 | Python 3.x |
| java | 62 | Java (OpenJDK) |
| cpp | 54 | C++ (GCC) |
| javascript | 63 | JavaScript (Node.js) |

Backend discovers labels via `GET /languages` and rejects unknown IDs from the client.

---

## 12. Security expectations

- No student `subprocess` / `exec` / `eval` in FastAPI
- Auth token only FastAPI → Judge0
- Hidden test stdin/stdout/expected never returned on Submit
- Sanitized compile/runtime messages
- Job Ready Redis = rate/concurrency only; **not** Judge0 Redis

---

## 13. Upgrade / backup

1. Read CE release notes for the next **pinned** tag.
2. Backup Judge0 Postgres volume.
3. Deploy new zip/tag on the VPS only.
4. Re-run live + smoke checks.
5. Do not couple upgrades to Job Ready app deploys.
