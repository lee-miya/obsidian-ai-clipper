import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from src.main import app
from src.config import Settings


@pytest.fixture
def settings(tmp_path):
    return Settings(database_path=str(tmp_path / "test.db"), vault_path=str(tmp_path))


@pytest_asyncio.fixture
async def client(monkeypatch, settings):
    from src.web import routes
    monkeypatch.setattr(routes, "settings", settings)
    store = routes.JobStore(settings.database_path)
    await store.init()
    monkeypatch.setattr(routes, "store", store)
    return TestClient(app)


class TestWebList:
    def test_web_list(self, client):
        response = client.get("/web")
        assert response.status_code == 200

    def test_web_list_empty(self, client):
        response = client.get("/web")
        assert response.status_code == 200
        assert "剪藏列表" in response.text


class TestWebDetail:
    def test_clip_detail_not_found(self, client):
        response = client.get("/web/clips/nonexistent")
        assert response.status_code == 404


class TestWebFailed:
    def test_failed_empty(self, client):
        response = client.get("/web/failed")
        assert response.status_code == 200
        assert "失败任务" in response.text


class TestWebQueue:
    def test_queue_status(self, client):
        response = client.get("/web/queue")
        assert response.status_code == 200
        assert "队列状态" in response.text
