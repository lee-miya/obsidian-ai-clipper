import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from src.main import app
from src.config import Settings
from src.api import deps
from src.api import routes


@pytest.fixture
def rate_limit_settings(tmp_path):
    return Settings(
        api_keys=["test-key"],
        database_path=str(tmp_path / "test.db"),
        vault_path=str(tmp_path),
    )


@pytest_asyncio.fixture
async def rate_limit_client(monkeypatch, rate_limit_settings):
    # Clear the in-memory rate limit buckets before each test
    deps.ip_requests.clear()
    deps.global_requests.clear()
    monkeypatch.setattr(deps, "settings", rate_limit_settings)
    monkeypatch.setattr(routes, "settings", rate_limit_settings)
    store = routes.JobStore(rate_limit_settings.database_path)
    await store.init()
    monkeypatch.setattr(routes, "store", store)
    return TestClient(app)


class TestRateLimit:
    def test_rate_limit_after_many_requests(self, rate_limit_client):
        client = rate_limit_client
        for i in range(10):
            response = client.post(
                "/api/clip",
                json={"url": "https://example.com"},
                headers={"Authorization": "Bearer test-key"},
            )
        response = client.post(
            "/api/clip",
            json={"url": "https://example.com"},
            headers={"Authorization": "Bearer test-key"},
        )
        assert response.status_code == 429

    def test_global_rate_limit(self, rate_limit_client):
        client = rate_limit_client
        for i in range(100):
            client.post(
                "/api/clip",
                json={"url": "https://example.com"},
                headers={"Authorization": "Bearer test-key"},
            )
        response = client.post(
            "/api/clip",
            json={"url": "https://example.com"},
            headers={"Authorization": "Bearer test-key"},
        )
        assert response.status_code == 429

    def test_security_headers_present(self, rate_limit_client):
        response = rate_limit_client.get("/health")
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["Content-Security-Policy"] == "default-src 'self'"

    def test_unauthorized_requests_not_counted(self, rate_limit_client):
        """Verify that unauthorized requests do not count toward rate limits."""
        client = rate_limit_client
        for i in range(20):
            client.post(
                "/api/clip",
                json={"url": "https://example.com"},
            )
        # After 20 unauthorized requests, a valid request should still work
        response = client.post(
            "/api/clip",
            json={"url": "https://example.com"},
            headers={"Authorization": "Bearer test-key"},
        )
        assert response.status_code == 202
