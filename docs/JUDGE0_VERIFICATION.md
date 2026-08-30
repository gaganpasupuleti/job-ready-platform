# Judge0 production verification checklist

Use **before** setting Railway `JUDGE0_ENABLED=true` for real students (or immediately after enabling in a controlled window).

Checkpoint: Build 4.2 / commit `a903c1d`.

## Preconditions

- [ ] Ubuntu 22.04 VPS with `systemd.unified_cgroup_hierarchy=0` applied and rebooted
- [ ] Official `judge0-v1.13.1` stack healthy (`db`, `redis`, `server`, `workers`)
- [ ] API reachable only via HTTPS reverse proxy (or tightly firewalled IP)
- [ ] `AUTHN_TOKEN` configured; same value ready for Railway `JUDGE0_AUTH_TOKEN`
- [ ] Railway backend vars prepared but not yet flipped for all traffic (optional staging)

## Live pytest

```powershell
cd backend
$env:JUDGE0_LIVE_TESTS = "1"
$env:JUDGE0_ENABLED = "true"
$env:JUDGE0_URL = "https://judge.yourdomain.com"   # or temporary allowlisted URL
$env:JUDGE0_AUTH_HEADER = "X-Auth-Token"
$env:JUDGE0_AUTH_TOKEN = "<secret>"
python -m pytest tests/test_judge0_live.py -q --tb=short
```

| Case | Pass |
|------|------|
| Python Accepted | ☐ |
| Python Wrong Answer | ☐ |
| Python Runtime Error | ☐ |
| Java compile/run | ☐ |
| C++ compile/run | ☐ |
| JavaScript run | ☐ |
| TLE / infinite loop | ☐ |
| Isolation (no Job Ready env leak) | ☐ |

## Manual product checks (DSA workspace)

| Case | Pass |
|------|------|
| Accepted | ☐ |
| Wrong Answer | ☐ |
| Compilation Error | ☐ |
| Runtime Error | ☐ |
| Time Limit Exceeded | ☐ |
| Public Run shows input / expected / actual | ☐ |
| Submit: hidden I/O not in response | ☐ |
| Stop Judge0 → Run/Submit unavailable / 503 | ☐ |
| Auth + MCQ + SQL still OK during outage | ☐ |

## Railway cutover

- [ ] `JUDGE0_ENABLED=true`
- [ ] `JUDGE0_URL=https://…`
- [ ] `JUDGE0_AUTH_HEADER=X-Auth-Token`
- [ ] `JUDGE0_AUTH_TOKEN` set (not in frontend)
- [ ] Poll/timeout vars set
- [ ] Backend redeployed
- [ ] `GET /api/v1/coding/execution-status` → `available: true`
- [ ] Admin coding page shows languages ✓

## Sign-off

| Field | Value |
|-------|--------|
| Judge0 host | |
| Judge0 version | 1.13.1 |
| Verified by | |
| Date | |
| Notes | |
