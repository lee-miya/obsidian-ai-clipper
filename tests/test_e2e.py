import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from src.main import app


@pytest_asyncio.fixture
async def client(tmp_path, monkeypatch):
    from src.config import Settings
    from src.api import deps, routes

    vault_path = tmp_path / "vault"
    vault_path.mkdir(parents=True, exist_ok=True)
    db_path = tmp_path / "e2e.db"

    settings = Settings(
        api_keys=["e2e-key"],
        kimi_api_key="fake-key",
        vault_path=str(vault_path),
        database_path=str(db_path),
    )
    from src.worker import worker
    monkeypatch.setattr(deps, "settings", settings)
    monkeypatch.setattr(routes, "settings", settings)
    monkeypatch.setattr(worker, "settings", settings)

    store = routes.JobStore(settings.database_path)
    await store.init()
    monkeypatch.setattr(routes, "store", store)

    return TestClient(app)


def test_create_clip(client, respx_mock):
    respx_mock.get("https://example.com/e2e").respond(
        200, text="<html><title>E2E</title><body>Content</body></html>"
    )
    respx_mock.post("https://api.moonshot.cn/v1/chat/completions").respond(
        json={
            "choices": [
                {
                    "message": {
                        "content": '{"title":"E2E","category":"未分类","tags":[],"summary":"","content_markdown":"Content","author":"","published_at":""}'
                    }
                }
            ]
        }
    )

    response = client.post(
        "/api/clip",
        json={"url": "https://example.com/e2e"},
        headers={"Authorization": "Bearer e2e-key"},
    )
    assert response.status_code == 202
    data = response.json()
    assert data["job_id"].startswith("clip_")
