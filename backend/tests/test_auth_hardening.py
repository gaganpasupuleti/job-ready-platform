"""Sprint 1 reliability: production seed guard + login throttle."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.config import settings
from app.models.enums import UserRole
from app.seed.runner import ensure_seed_admin
from app.services.auth_throttle import reset_memory_throttle_for_tests


@pytest.fixture(autouse=True)
def _reset_throttle():
    reset_memory_throttle_for_tests()
    yield
    reset_memory_throttle_for_tests()


@pytest.mark.asyncio
async def test_production_seed_refuses_default_admin(monkeypatch):
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "admin_bootstrap_email", "")
    monkeypatch.setattr(settings, "admin_bootstrap_password", "")

    session = MagicMock()
    empty = MagicMock()
    empty.scalar_one_or_none.return_value = None
    session.execute = AsyncMock(return_value=empty)
    session.add = MagicMock()
    session.flush = AsyncMock()

    result = await ensure_seed_admin(session)
    assert result is None
    session.add.assert_not_called()


@pytest.mark.asyncio
async def test_production_seed_allows_explicit_bootstrap(monkeypatch):
    monkeypatch.setattr(settings, "app_env", "production")
    email = f"bootstrap_{uuid.uuid4().hex[:8]}@example.com"
    monkeypatch.setattr(settings, "admin_bootstrap_email", email)
    monkeypatch.setattr(settings, "admin_bootstrap_password", "SecureBootstrap1!")

    session = MagicMock()
    empty = MagicMock()
    empty.scalar_one_or_none.return_value = None
    session.execute = AsyncMock(return_value=empty)
    session.add = MagicMock()
    session.flush = AsyncMock()

    admin = await ensure_seed_admin(session)
    assert admin is not None
    assert admin.email == email
    assert admin.role == UserRole.ADMIN
    session.add.assert_called_once()


@pytest.mark.asyncio
async def test_login_throttle_blocks_after_failures(client, monkeypatch):
    monkeypatch.setattr(settings, "login_max_failures", 3)
    monkeypatch.setattr(settings, "login_failure_window_seconds", 300)
    reset_memory_throttle_for_tests()

    suffix = uuid.uuid4().hex[:8]
    email = f"throttle_{suffix}@example.com"
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": f"throttle_{suffix}",
            "password": "Password123!",
        },
    )

    for _ in range(3):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "WrongPassword!"},
        )
        assert resp.status_code == 401

    blocked = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "WrongPassword!"},
    )
    assert blocked.status_code == 429

    still = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    assert still.status_code == 429
