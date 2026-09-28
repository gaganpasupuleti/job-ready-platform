import asyncio
import uuid
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from app.content.studio_batch import apply_batch
from app.db.session import AsyncSessionLocal, engine
from app.main import app
from app.utils import redis as redis_module

SATURDAY_BATCH = Path(__file__).resolve().parents[1] / "content" / "batches" / "2026-09-19-saturday-001"


async def _load_saturday_batch() -> None:
    async with AsyncSessionLocal() as db:
        result = await apply_batch(db, SATURDAY_BATCH, allow_remote=False)
        if result.get("refused"):
            raise RuntimeError(result)
        await db.commit()
    await engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def saturday_batch_loaded():
    """CI starts from seed only. The studio tests need the reviewed Saturday batch."""
    asyncio.run(_load_saturday_batch())


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
