import uuid

import pytest


@pytest.mark.asyncio
async def test_register_and_login(client):
    suffix = uuid.uuid4().hex[:8]
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"newuser_{suffix}@example.com",
            "username": f"newuser_{suffix}",
            "full_name": "New User",
            "password": "Password123!",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["access_token"]
    assert data["user"]["role"] == "student"


@pytest.mark.asyncio
async def test_login_invalid_password(client):
    suffix = uuid.uuid4().hex[:8]
    email = f"loginfail_{suffix}@example.com"
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": f"loginfail_{suffix}",
            "password": "Password123!",
        },
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "WrongPassword!"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_requires_auth(client):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_with_token(client, student_auth):
    headers, email = student_auth
    response = await client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == email
