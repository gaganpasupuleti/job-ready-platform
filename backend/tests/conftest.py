import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.db.session import engine
from app.main import app
from app.utils import redis as redis_module


@pytest.fixture(autouse=True)
async def reset_connections():
    yield
    await redis_module.close_redis()
    await engine.dispose()


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def student_auth(client):
    suffix = uuid.uuid4().hex[:8]
    email = f"student_{suffix}@example.com"
    password = "Student123!"
    register = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": f"student_{suffix}",
            "full_name": "Test Student",
            "password": password,
        },
    )
    assert register.status_code == 200, register.text
    token = register.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, email


@pytest.fixture
async def admin_auth(client):
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@jobready.dev", "password": "Admin123!"},
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
