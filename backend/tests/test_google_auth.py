import uuid

import pytest
from sqlalchemy import func, select

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.enums import UserRole
from app.models.user import User
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


@pytest.mark.asyncio
async def test_google_signup_creates_student_and_reuses_subject(client, google_ready):
    email = f"google_{uuid.uuid4().hex[:8]}@example.com"
    subject = f"sub-new-{uuid.uuid4().hex}"
    google_ready(GoogleProfile(subject=subject, email=email, name="Ada Lovelace"))

    created = await client.post("/api/v1/auth/google", json={"credential": "aaa.bbb.ccc"})
    assert created.status_code == 200, created.text
    body = created.json()
    assert body["is_new_user"] is True
    assert body["user"]["role"] == "student"
    assert body["user"]["email"] == email
    assert body["access_token"]
    assert body["user"]["username"]

    again = await client.post("/api/v1/auth/google", json={"credential": "aaa.bbb.ccc"})
    assert again.status_code == 200
    assert again.json()["is_new_user"] is False
    assert again.json()["user"]["id"] == body["user"]["id"]
    assert await _user_count(email) == 1

    password = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "whatever-password"},
    )
    assert password.status_code == 401


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

    google_ready(
        GoogleProfile(subject=f"sub-link-{uuid.uuid4().hex}", email=email, name="Existing Student")
    )
    linked = await client.post("/api/v1/auth/google", json={"credential": "aaa.bbb.ccc"})
    assert linked.status_code == 200, linked.text
    assert linked.json()["user"]["id"] == user_id
    assert linked.json()["is_new_user"] is False
    assert linked.json()["user"]["role"] == "student"
    assert await _user_count(email) == 1

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
    assert created.status_code == 200
    assert created.json()["user"]["role"] == UserRole.STUDENT.value

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
async def test_google_inactive_account_stays_blocked(client, google_ready):
    email = f"inactive_{uuid.uuid4().hex[:8]}@example.com"
    google_ready(
        GoogleProfile(subject=f"sub-inactive-{uuid.uuid4().hex}", email=email, name="Inactive")
    )
    created = await client.post("/api/v1/auth/google", json={"credential": "aaa.bbb.ccc"})
    assert created.status_code == 200
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
