# Task 15 Brief

Source plan: docs/superpowers/plans/2026-06-21-obsidian-ai-clipper-plan.md

## Task 15: Integration and End-to-End Test

**Files:**
- Create: `tests/test_e2e.py`

**Interfaces:**
- Consumes: full API pipeline.
- Produces: end-to-end test verifying clip creation and processing.

- [ ] **Step 1: Write end-to-end test**

```python
import pytest
from fastapi.testclient import TestClient
from src.main import app

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "e2e.db"))
    monkeypatch.setenv("VAULT_PATH", str(tmp_path / "vault"))
    monkeypatch.setenv("API_KEYS", "e2e-key")
    monkeypatch.setenv("KIMI_API_KEY", "fake-key")
    return TestClient(app)

def test_create_clip(client, respx_mock):
    respx_mock.get("https://example.com/e2e").respond(200, text="<html><title>E2E</title><body>Content</body></html>")
    respx_mock.post("https://api.moonshot.cn/v1/chat/completions").respond(json={
        "choices": [{"message": {"content": '{"title":"E2E","category":"未分类","tags":[],"summary":"","content_markdown":"Content","author":"","published_at":""}'}}]
    })

    response = client.post("/api/clip", json={"url": "https://example.com/e2e"}, headers={"Authorization": "Bearer e2e-key"})
    assert response.status_code == 202
    data = response.json()
    assert data["job_id"].startswith("clip_")
```

- [ ] **Step 2: Run end-to-end test**

Run: `pytest tests/test_e2e.py -v`  
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_e2e.py
git commit -m "test: add end-to-end clip test"
```

---

