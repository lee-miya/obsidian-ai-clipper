import pytest
from src.core.storage import JobStore
from src.worker.worker import process_job
from src.config import Settings

async def test_process_job_success(tmp_path, monkeypatch, respx_mock):
    db_path = tmp_path / "test.db"
    store = JobStore(str(db_path))
    await store.init()

    respx_mock.get("https://example.com").respond(200, text="<html><head><title>T</title></head><body><p>Hello world, this is a longer content that should pass the 50 character minimum threshold for processing. It needs to be at least fifty characters long to avoid the needs_review status.</p></body></html>")
    respx_mock.post("https://api.moonshot.cn/v1/chat/completions").respond(json={
        "choices": [{"message": {"content": '{"title":"T","category":"未分类","tags":[],"summary":"S","content_markdown":"Hello","author":"","published_at":""}'}}]
    })

    monkeypatch.setenv("VAULT_PATH", str(tmp_path / "vault"))
    monkeypatch.setenv("KIMI_API_KEY", "test-kimi-key")
    monkeypatch.setenv("API_KEYS", "test-key-1,test-key-2")
    job = await store.create_job("https://example.com")
    await process_job(job["id"], store)
    updated = await store.get_job(job["id"])
    assert updated["status"] == "done"
    assert updated["vault_path"] is not None
