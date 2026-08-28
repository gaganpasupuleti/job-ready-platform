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
    assert data["status"] == "ok"
    assert data["service"] == "job-ready-platform-api"


@pytest.mark.asyncio
async def test_modules_endpoint(client):
    response = await client.get("/api/v1/modules")
    assert response.status_code == 200
    data = response.json()
    assert "modules" in data
    assert len(data["modules"]) > 0
    assert all("id" in m and "name" in m for m in data["modules"])
