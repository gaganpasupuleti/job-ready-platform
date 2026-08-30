#!/usr/bin/env python3
"""Deployment smoke checks. Prints no credentials.

Usage:
  python scripts/smoke.py
  python scripts/smoke.py --base-url https://api.example.com
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request


def _get(url: str, timeout: float = 10.0) -> tuple[int, dict | list | str]:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            try:
                return resp.status, json.loads(body)
            except json.JSONDecodeError:
                return resp.status, body
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            return exc.code, json.loads(body)
        except json.JSONDecodeError:
            return exc.code, body


def main() -> int:
    parser = argparse.ArgumentParser(description="Job Ready Platform smoke checks")
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000",
        help="API base URL (no trailing slash)",
    )
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    failures: list[str] = []

    checks = [
        ("health", f"{base}/api/v1/health"),
        ("modules", f"{base}/api/v1/modules"),
        ("sql execution status", f"{base}/api/v1/sql/execution-status"),
        ("auth login route exists", f"{base}/api/v1/auth/login"),
    ]

    for name, url in checks:
        try:
            status, payload = _get(url)
            if name == "auth login route exists":
                # POST-only endpoints may return 405/422 on GET — that still proves the route exists.
                ok = status in {200, 405, 422, 401, 403}
            elif name == "sql execution status":
                ok = status in {200, 401}
            else:
                ok = status == 200
            print(f"[{'OK' if ok else 'FAIL'}] {name}: HTTP {status}")
            if name == "health" and isinstance(payload, dict):
                print(f"       status={payload.get('status')} checks={payload.get('checks')}")
                blob = json.dumps(payload).lower()
                if "password" in blob or "postgresql://" in blob:
                    failures.append("health response appears to leak secrets")
            if not ok:
                failures.append(f"{name} returned {status}")
        except Exception as exc:  # noqa: BLE001
            print(f"[FAIL] {name}: {exc}")
            failures.append(f"{name}: {exc}")

    # Catalog requires auth — only verify the unauthenticated response is not a 500.
    try:
        status, _ = _get(f"{base}/api/v1/practice/catalog")
        ok = status in {200, 401, 403}
        print(f"[{'OK' if ok else 'FAIL'}] practice catalog probe: HTTP {status}")
        if not ok:
            failures.append(f"practice catalog returned {status}")
    except Exception as exc:  # noqa: BLE001
        print(f"[FAIL] practice catalog probe: {exc}")
        failures.append(str(exc))

    if failures:
        print("Smoke FAILED:")
        for item in failures:
            print(f" - {item}")
        return 1
    print("Smoke PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
