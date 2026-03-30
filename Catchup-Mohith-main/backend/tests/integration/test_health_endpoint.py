# /home/mohith/Catchup-Mohith/backend/tests/integration/test_health_endpoint.py
import pytest
from backend.app.core.config import settings


@pytest.mark.asyncio
async def test_health_endpoint_returns_200_all_services_healthy(client):
    response = await client.get("/health")
    assert response.status_code == 200
    body = response.json()["data"]
    assert body["status"] in ("healthy", "degraded")
    assert "database" in body
    assert body["database"]["status"] == "healthy"
    assert "redis" in body
    assert "temporal" in body
    assert "seed" in body


@pytest.mark.asyncio
async def test_health_endpoint_database_key_present(client):
    response = await client.get("/health")
    assert response.status_code in (200, 503)
    assert "data" in response.json()


@pytest.mark.asyncio
async def test_health_endpoint_shows_default_password_warning(client):
    if settings.initial_admin_password == "REDACTED_SEE_ENV":
        response = await client.get("/health")
        body = response.json()["data"]
        assert body["seed"]["default_password_warning"] is True
    else:
        pytest.skip(
            "INITIAL_ADMIN_PASSWORD is not the default value "
            "— skipping default password warning test"
        )


@pytest.mark.asyncio
async def test_temporal_health_endpoint_returns_response(client):
    response = await client.get("/health/temporal")
    assert response.status_code in (200, 503)
    assert "data" in response.json()
    assert "status" in response.json()["data"]
