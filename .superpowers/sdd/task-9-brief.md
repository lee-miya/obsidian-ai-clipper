# Task 9 Brief

Source plan: docs/superpowers/plans/2026-06-21-obsidian-ai-clipper-plan.md

## Task 9: Background Worker

**Files:**
- Create: `src/worker/worker.py`
- Test: `tests/test_worker.py`

**Interfaces:**
- Produces: `async process_job(job_id: str, store: JobStore)`.

- [ ] **Step 1: Write failing test**

```python
import pytest
from src.core.storage import JobStore
from src.worker.worker import process_job
from src.config import Settings

async def test_process_job_success(tmp_path, monkeypatch, respx_mock):
    db_path = tmp_path / "test.db"
    store = JobStore(str(db_path))
    await store.init()

    respx_mock.get("https://example.com").respond(200, text="<html><head><title>T</title></head><body><p>Hello</p></body></html>")
    respx_mock.post("https://api.moonshot.cn/v1/chat/completions").respond(json={
        "choices": [{"message": {"content": '{"title":"T","category":"未分类","tags":[],"summary":"S","content_markdown":"Hello","author":"","published_at":""}'}}]
    })

    monkeypatch.setattr(Settings, "vault_path", str(tmp_path / "vault"))
    job = await store.create_job("https://example.com")
    await process_job(job["id"], store)
    updated = await store.get_job(job["id"])
    assert updated["status"] == "done"
    assert updated["vault_path"] is not None
```

- [ ] **Step 2: Implement `src/worker/worker.py`**

```python
import asyncio
import json
from pathlib import Path
from src.config import Settings
from src.core.models import JobStatus
from src.core.storage import JobStore
from src.fetcher.fetcher import fetch_html
from src.extractor.extractor import extract
from src.ai.kimi_client import KimiClient
from src.writer.vault_writer import save_clip

settings = Settings()

async def _save_raw_html(job_id: str, html: str) -> str:
    raw_dir = Path(settings.vault_path) / ".clipper-tmp"
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / f"{job_id}.html"
    path.write_text(html, encoding="utf-8")
    return str(path)

async def _save_extracted(job_id: str, extracted) -> str:
    raw_dir = Path(settings.vault_path) / ".clipper-tmp"
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / f"{job_id}.json"
    path.write_text(json.dumps({
        "title": extracted.title,
        "content": extracted.content,
        "images": extracted.images,
        "code_blocks": extracted.code_blocks,
        "author": extracted.author,
        "published_at": extracted.published_at,
    }, ensure_ascii=False), encoding="utf-8")
    return str(path)

async def process_job(job_id: str, store: JobStore):
    job = await store.get_job(job_id)
    if not job:
        return

    url = job["url"]

    try:
        await store.update_status(job_id, JobStatus.FETCHING, stage="fetching")
        html = await fetch_html(url)
        raw_html_path = await _save_raw_html(job_id, html)

        await store.update_status(job_id, JobStatus.EXTRACTING, stage="extracting", raw_html_path=raw_html_path)
        extracted = extract(html, url)
        extracted_json_path = await _save_extracted(job_id, extracted)

        if not extracted.content or len(extracted.content.strip()) < 50:
            await store.update_status(job_id, JobStatus.NEEDS_REVIEW, stage="extracting", last_error="Content too short", extracted_json_path=extracted_json_path)
            return

        await store.update_status(job_id, JobStatus.AI_PROCESSING, stage="ai_processing", extracted_json_path=extracted_json_path)
        client = KimiClient(api_key=settings.kimi_api_key, model=settings.kimi_model)

        last_error = None
        for attempt in range(settings.max_retry):
            try:
                ai_result = await client.process(extracted, url=url)
                break
            except Exception as e:
                last_error = str(e)
                await asyncio.sleep(2 ** attempt)
        else:
            ai_result = {
                "title": extracted.title or url,
                "category": "未分类",
                "tags": [],
                "summary": "",
                "content_markdown": extracted.content,
                "author": extracted.author,
                "published_at": extracted.published_at,
            }

        await store.update_status(job_id, JobStatus.SAVING, stage="saving")
        vault_path = await save_clip(job_id, url, ai_result, extracted, settings.vault_path)

        await store.update_status(job_id, JobStatus.DONE, stage="done", vault_path=str(vault_path))

    except Exception as e:
        retry_count = job["retry_count"] + 1
        if retry_count < job["max_retries"]:
            await store.update_status(job_id, JobStatus.PENDING, stage="pending", retry_count=retry_count, last_error=str(e))
        else:
            await store.update_status(job_id, JobStatus.FAILED, stage="failed", retry_count=retry_count, last_error=str(e))
```

- [ ] **Step 3: Run worker tests**

Run: `pytest tests/test_worker.py -v`  
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add src/worker/worker.py tests/test_worker.py
git commit -m "feat: add background job worker"
```

---

