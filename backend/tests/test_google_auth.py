import uuid

import pytest
from sqlalchemy import func, select

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.auth_identity import UserAuthIdentity
from app.models.enums import UserRole
from app.models.user import User
from app.services.auth_policy import GOOGLE_ACCESS_DENIED, REGISTRATION_CLOSED
from app.services.google_identity import GoogleProfile, GoogleTokenError, verify_google_id_token


def _claims(**overrides):
    payload = {
        "iss": "https://accounts.google.com",
        "aud": "test-client",
        "email": "google.user@example.com",
        "email_verified": True,
        "sub": "google-subject-1",
        "name": "Google User",
        "role": "admin",
    }
    payload.update(overrides)
    return payload


def _decode_factory(claims=None, error: GoogleTokenError | None = None):
    def decode(_credential: str, _client_id: str):
        if error is not None:
            raise error
        return claims or _claims()

    return decode


def test_google_token_transport_is_installed():
    from google.auth.transport import requests as google_requests

    assert google_requests.Request is not None


@pytest.mark.asyncio
async def test_google_token_checks_do_not_call_google():
    profile = verify_google_id_token("aaa.bbb.ccc", "test-client", decode=_decode_factory())
    assert profile.subject == "google-subject-1"
    assert profile.email == "google.user@example.com"

    with pytest.raises(GoogleTokenError) as malformed:
        verify_google_id_token("not-a-token", "test-client", decode=_decode_factory())
    assert malformed.value.reason == "malformed"

    with pytest.raises(GoogleTokenError) as audience:
        verify_google_id_token(
            "aaa.bbb.ccc",
            "test-client",
            decode=_decode_factory(_claims(aud="other")),
        )
    assert audience.value.reason == "audience"

    with pytest.raises(GoogleTokenError) as unverified:
        verify_google_id_token(
            "aaa.bbb.ccc",
            "test-client",
            decode=_decode_factory(_claims(email_verified=False)),
        )
    assert unverified.value.reason == "unverified"

    with pytest.raises(GoogleTokenError) as expired:
        verify_google_id_token(
            "aaa.bbb.ccc",
            "test-client",
            decode=_decode_factory(error=GoogleTokenError("expired")),
        )
    assert expired.value.reason == "expired"

    with pytest.raises(GoogleTokenError) as invalid:
        verify_google_id_token(
            "aaa.bbb.ccc",
            "test-client",
            decode=_decode_factory(error=ValueError("bad signature")),
        )
    assert invalid.value.reason == "invalid"


@pytest.fixture
def google_ready(monkeypatch):
    monkeypatch.setattr(settings, "google_client_id", "test-client")

    def install(profile: GoogleProfile):
        def fake_verify(credential: str, client_id: str):
            if credential.count(".") != 2:
                raise GoogleTokenError("malformed")
            if credential == "bad-signature":
                raise GoogleTokenError("invalid")
            if credential == "expired-token":
                raise GoogleTokenError("expired")
            if credential == "wrong-audience":
                raise GoogleTokenError("audience")
            if credential == "unverified-email":
                raise GoogleTokenError("unverified")
            if client_id != "test-client":
                raise GoogleTokenError("audience")
            return profile

        monkeypatch.setattr("app.services.auth_service.verify_google_id_token", fake_verify)

    return install


async def _user_count(email: str) -> int:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(func.count()).select_from(User).where(User.email == email))
        return int(result.scalar_one())


async def _identity_count(subject: str) -> int:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(func.count())
            .select_from(UserAuthIdentity)
            .where(UserAuthIdentity.provider_subject == subject)
        )
        return int(result.scalar_one())


@pytest.mark.asyncio
async def test_google_does_not_create_accounts(client, google_ready):
    email = f"google_{uuid.uuid4().hex[:8]}@example.com"
    subject = f"sub-new-{uuid.uuid4().hex}"
    google_ready(GoogleProfile(subject=subject, email=email, name="Ada Lovelace"))

    rejected = await client.post("/api/v1/auth/google", json={"credential": "aaa.bbb.ccc"})
    assert rejected.status_code == 403, rejected.text
    assert rejected.json()["detail"] == GOOGLE_ACCESS_DENIED
    assert "access_token" not in rejected.json()
    assert await _user_count(email) == 0
    assert await _identity_count(subject) == 0


@pytest.mark.asyncio
async def test_google_links_existing_verified_email_without_duplicate(client, google_ready):
    suffix = uuid.uuid4().hex[:8]
    email = f"link_{suffix}@example.com"
    registered = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": f"link_{suffix}",
            "full_name": "Existing Student",
            "password": "Password123!",
        },
    )
    assert registered.status_code == 200, registered.text
    user_id = registered.json()["user"]["id"]

    subject = f"sub-link-{uuid.uuid4().hex}"
    google_ready(GoogleProfile(subject=subject, email=email, name="Existing Student"))
    linked = await client.post("/api/v1/auth/google", json={"credential": "aaa.bbb.ccc"})
    assert linked.status_code == 200, linked.text
    assert linked.json()["user"]["id"] == user_id
    assert linked.json()["is_new_user"] is False
    assert linked.json()["user"]["role"] == "student"
    assert await _user_count(email) == 1
    assert await _identity_count(subject) == 1

    again = await client.post("/api/v1/auth/google", json={"credential": "aaa.bbb.ccc"})
    assert again.status_code == 200, again.text
    assert again.json()["user"]["id"] == user_id
    assert again.json()["is_new_user"] is False
    assert await _identity_count(subject) == 1

    password = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    assert password.status_code == 200


@pytest.mark.asyncio
async def test_google_rejects_bad_tokens_and_cannot_grant_admin(client, google_ready):
    email = f"adminish_{uuid.uuid4().hex[:8]}@example.com"
    google_ready(
        GoogleProfile(subject=f"sub-admin-{uuid.uuid4().hex}", email=email, name="Nope")
    )
    created = await client.post("/api/v1/auth/google", json={"credential": "aaa.bbb.ccc"})
    assert created.status_code == 403
    assert "access_token" not in created.json()
    assert await _user_count(email) == 0

    rejected_credentials = (
        "bad-signature",
        "expired-token",
        "wrong-audience",
        "unverified-email",
        "nope",
    )
    for credential in rejected_credentials:
        rejected = await client.post("/api/v1/auth/google", json={"credential": credential})
        assert rejected.status_code == 401, credential

    empty = await client.post("/api/v1/auth/google", json={"credential": ""})
    assert empty.status_code == 422


@pytest.mark.asyncio
async def test_google_does_not_link_or_login_non_student(client, google_ready):
    for role in (UserRole.ADMIN, UserRole.TRAINER):
        suffix = uuid.uuid4().hex[:8]
        email = f"{role.value}_{suffix}@example.com"
        registered = await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "username": f"{role.value}_{suffix}",
                "password": "Password123!",
            },
        )
        assert registered.status_code == 200, registered.text
        async with AsyncSessionLocal() as db:
            user = (await db.execute(select(User).where(User.email == email))).scalar_one()
            user.role = role
            await db.commit()
            user_id = user.id

        google_ready(
            GoogleProfile(
                subject=f"sub-{role.value}-{uuid.uuid4().hex}",
                email=email,
                name="Privileged",
            )
        )
        rejected = await client.post("/api/v1/auth/google", json={"credential": "aaa.bbb.ccc"})
        assert rejected.status_code == 403, rejected.text
        assert "access_token" not in rejected.json()

        async with AsyncSessionLocal() as db:
            identity = (
                await db.execute(
                    select(UserAuthIdentity).where(UserAuthIdentity.user_id == user_id)
                )
            ).scalar_one_or_none()
            assert identity is None
            stored = (await db.execute(select(User).where(User.id == user_id))).scalar_one()
            assert stored.role == role
        assert await _user_count(email) == 1

        password = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "Password123!"},
        )
        assert password.status_code == 200
        assert password.json()["user"]["role"] == role.value


@pytest.mark.asyncio
async def test_google_inactive_account_stays_blocked(client, google_ready):
    suffix = uuid.uuid4().hex[:8]
    email = f"inactive_{suffix}@example.com"
    registered = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "username": f"inactive_{suffix}", "password": "Password123!"},
    )
    assert registered.status_code == 200, registered.text
    google_ready(
        GoogleProfile(subject=f"sub-inactive-{uuid.uuid4().hex}", email=email, name="Inactive")
    )
    async with AsyncSessionLocal() as db:
        user = (await db.execute(select(User).where(User.email == email))).scalar_one()
        user.is_active = False
        await db.commit()

    blocked = await client.post("/api/v1/auth/google", json={"credential": "aaa.bbb.ccc"})
    assert blocked.status_code == 403


@pytest.mark.asyncio
async def test_google_unconfigured_does_not_break_password_login(client, monkeypatch):
    monkeypatch.setattr(settings, "google_client_id", "")
    missing = await client.post("/api/v1/auth/google", json={"credential": "aaa.bbb.ccc"})
    assert missing.status_code == 503

    suffix = uuid.uuid4().hex[:8]
    email = f"stillpass_{suffix}@example.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "username": f"stillpass_{suffix}", "password": "Password123!"},
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    assert login.status_code == 200


@pytest.mark.asyncio
async def test_public_registration_can_be_closed_and_reopened(client, monkeypatch):
    suffix = uuid.uuid4().hex[:8]
    payload = {
        "email": f"closed_{suffix}@example.com",
        "username": f"closed_{suffix}",
        "password": "Password123!",
    }
    monkeypatch.setattr(settings, "public_registration_enabled", False)
    closed = await client.post("/api/v1/auth/register", json=payload)
    assert closed.status_code == 403, closed.text
    assert closed.json()["detail"] == REGISTRATION_CLOSED
    assert "access_token" not in closed.json()
    assert await _user_count(payload["email"]) == 0
    config = await client.get("/api/v1/auth/config")
    assert config.status_code == 200
    assert config.json()["public_registration_enabled"] is False

    monkeypatch.setattr(settings, "public_registration_enabled", True)
    opened = await client.post("/api/v1/auth/register", json=payload)
    assert opened.status_code == 200, opened.text
    assert opened.json()["user"]["role"] == "student"
    assert await _user_count(payload["email"]) == 1


@pytest.mark.asyncio
async def test_password_login_is_limited_to_admin_and_approved_emails(client, monkeypatch):
    suffix = uuid.uuid4().hex[:8]
    ordinary = f"ordinary_{suffix}@example.com"
    approved = f"approved_{suffix}@example.com"
    admin_email = f"adminpw_{suffix}@example.com"
    password = "Password123!"
    for email, username in (
        (ordinary, f"ordinary_{suffix}"),
        (approved, f"approved_{suffix}"),
        (admin_email, f"adminpw_{suffix}"),
    ):
        created = await client.post(
            "/api/v1/auth/register",
            json={"email": email, "username": username, "password": password},
        )
        assert created.status_code == 200, created.text

    async with AsyncSessionLocal() as db:
        admin = (await db.execute(select(User).where(User.email == admin_email))).scalar_one()
        admin.role = UserRole.ADMIN
        await db.commit()

    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "password_login_emails", approved)

    blocked = await client.post("/api/v1/auth/login", json={"email": ordinary, "password": password})
    assert blocked.status_code == 401, blocked.text
    assert "access_token" not in blocked.json()

    allowed = await client.post("/api/v1/auth/login", json={"email": approved, "password": password})
    assert allowed.status_code == 200, allowed.text
    assert allowed.json()["user"]["role"] == "student"

    admin_login = await client.post(
        "/api/v1/auth/login",
        json={"email": admin_email, "password": password},
    )
    assert admin_login.status_code == 200, admin_login.text
    assert admin_login.json()["user"]["role"] == "admin"
