import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from src.main import app
from src.config import Settings


@pytest.fixture
def api_keys():
    return ["test-key-12345"]


@pytest.fixture
def settings(api_keys, tmp_path):
    return Settings(api_keys=api_keys, database_path=str(tmp_path / "test.db"), vault_path=str(tmp_path))


@pytest_asyncio.fixture
async def client(monkeypatch, settings):
    from src.api import deps
    from src.api import routes
    monkeypatch.setattr(deps, "settings", settings)
    monkeypatch.setattr(routes, "settings", settings)
    store = routes.JobStore(settings.database_path)
    await store.init()
    monkeypatch.setattr(routes, "store", store)
    return TestClient(app)


@pytest.fixture
def auth_headers(api_keys):
    return {"Authorization": f"Bearer {api_keys[0]}"}


class TestHealth:
    def test_health_ok(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestClipAuth:
    def test_clip_requires_auth(self, client):
        response = client.post("/api/clip", json={"url": "https://example.com"})
        assert response.status_code == 401

    def test_clip_wrong_key(self, client):
        response = client.post(
            "/api/clip",
            json={"url": "https://example.com"},
            headers={"Authorization": "Bearer wrong-key"},
        )
        assert response.status_code == 401

    def test_clip_no_bearer(self, client):
        response = client.post(
            "/api/clip",
            json={"url": "https://example.com"},
            headers={"Authorization": "no-bearer-prefix"},
        )
        assert response.status_code == 401


class TestClipValidation:
    def test_clip_rejects_invalid_url(self, client, auth_headers):
        response = client.post(
            "/api/clip",
            json={"url": "not-a-valid-url"},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_clip_rejects_localhost(self, client, auth_headers):
        response = client.post(
            "/api/clip",
            json={"url": "http://localhost:8080"},
            headers=auth_headers,
        )
        assert response.status_code == 400


class TestGetJob:
    def test_get_job_not_found(self, client, auth_headers):
        response = client.get("/api/jobs/nonexistent", headers=auth_headers)
        assert response.status_code == 404

    def test_get_job_requires_auth(self, client):
        response = client.get("/api/jobs/some-id")
        assert response.status_code == 401


class TestClipSuccess:
    def test_clip_accepts_valid_url(self, client, auth_headers):
        response = client.post(
            "/api/clip",
            json={"url": "https://example.com"},
            headers=auth_headers,
        )
        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "pending"

    def test_clip_duplicate_url(self, client, auth_headers):
        response1 = client.post(
            "/api/clip",
            json={"url": "https://example.com"},
            headers=auth_headers,
        )
        assert response1.status_code == 202

        response2 = client.post(
            "/api/clip",
            json={"url": "https://example.com"},
            headers=auth_headers,
        )
        assert response2.status_code == 409
