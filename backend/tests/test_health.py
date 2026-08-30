import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in {"ok", "degraded"}
    assert data["service"] == "job-ready-platform-api"
    assert "checks" in data
    assert "database" in data["checks"]
    assert "sql_sandbox" in data["checks"]
    assert "judge0" in data["checks"]
    # Public health must not leak connection strings
    blob = str(data).lower()
    assert "password" not in blob
    assert "postgresql://" not in blob
    assert "@localhost" not in blob


@pytest.mark.asyncio
async def test_modules_endpoint(client):
    response = await client.get("/api/v1/modules")
    assert response.status_code == 200
    data = response.json()
    assert "modules" in data
    assert len(data["modules"]) > 0
    assert all("id" in m and "name" in m for m in data["modules"])
