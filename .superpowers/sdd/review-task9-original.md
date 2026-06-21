226d13b feat: add background job worker
 src/config.py        | 18 ++++++++---
 src/worker/worker.py | 87 ++++++++++++++++++++++++++++++++++++++++++++++++++++
 tests/test_worker.py | 23 ++++++++++++++
 3 files changed, 124 insertions(+), 4 deletions(-)
diff --git a/src/config.py b/src/config.py
index bbec3e8..7a9aa0b 100644
--- a/src/config.py
+++ b/src/config.py
@@ -1,45 +1,55 @@
 import json
 import os
 from typing import Any
 
+from pydantic import Field
 from pydantic.fields import FieldInfo
-from pydantic_settings import BaseSettings, SettingsConfigDict, EnvSettingsSource, PydanticBaseSettingsSource
+from pydantic_settings import BaseSettings, SettingsConfigDict, EnvSettingsSource, DotEnvSettingsSource, PydanticBaseSettingsSource
 
 
 class CommaSeparatedEnvSource(EnvSettingsSource):
     def prepare_field_value(
         self, field_name: str, field: FieldInfo, value: Any, value_is_complex: bool
     ) -> Any:
         if field_name == 'api_keys' and isinstance(value, str):
             return [key.strip() for key in value.split(',')]
         return super().prepare_field_value(field_name, field, value, value_is_complex)
 
 
+class CommaSeparatedDotEnvSource(DotEnvSettingsSource):
+    def prepare_field_value(
+        self, field_name: str, field: FieldInfo, value: Any, value_is_complex: bool
+    ) -> Any:
+        if field_name == 'api_keys' and isinstance(value, str):
+            return [key.strip() for key in value.split(',')]
+        return super().prepare_field_value(field_name, field, value, value_is_complex)
+
+
 class Settings(BaseSettings):
     model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
 
-    api_keys: list[str]
-    kimi_api_key: str
+    api_keys: list[str] = Field(default_factory=list)
+    kimi_api_key: str = Field(default="")
     kimi_model: str = "kimi-k2.6"
     vault_path: str = "/data/vault"
     database_path: str = "/data/clipper.db"
     log_level: str = "INFO"
     rate_limit_ip: str = "10/minute"
     rate_limit_global: str = "100/minute"
     max_retry: int = 3
 
     @classmethod
     def settings_customise_sources(
         cls,
         settings_cls: type[BaseSettings],
         init_settings: PydanticBaseSettingsSource,
         env_settings: PydanticBaseSettingsSource,
         dotenv_settings: PydanticBaseSettingsSource,
         file_secret_settings: PydanticBaseSettingsSource,
     ) -> tuple[PydanticBaseSettingsSource, ...]:
         return (
             init_settings,
             CommaSeparatedEnvSource(settings_cls),
-            dotenv_settings,
+            CommaSeparatedDotEnvSource(settings_cls),
             file_secret_settings,
         )
diff --git a/src/worker/worker.py b/src/worker/worker.py
new file mode 100644
index 0000000..c0d03b7
--- /dev/null
+++ b/src/worker/worker.py
@@ -0,0 +1,87 @@
+import asyncio
+import json
+from pathlib import Path
+from src.config import Settings
+from src.core.models import JobStatus
+from src.core.storage import JobStore
+from src.fetcher.fetcher import fetch_html
+from src.extractor.extractor import extract
+from src.ai.kimi_client import KimiClient
+from src.writer.vault_writer import save_clip
+
+settings = Settings()
+
+async def _save_raw_html(job_id: str, html: str) -> str:
+    raw_dir = Path(settings.vault_path) / ".clipper-tmp"
+    raw_dir.mkdir(parents=True, exist_ok=True)
+    path = raw_dir / f"{job_id}.html"
+    path.write_text(html, encoding="utf-8")
+    return str(path)
+
+async def _save_extracted(job_id: str, extracted) -> str:
+    raw_dir = Path(settings.vault_path) / ".clipper-tmp"
+    raw_dir.mkdir(parents=True, exist_ok=True)
+    path = raw_dir / f"{job_id}.json"
+    path.write_text(json.dumps({
+        "title": extracted.title,
+        "content": extracted.content,
+        "images": extracted.images,
+        "code_blocks": extracted.code_blocks,
+        "author": extracted.author,
+        "published_at": extracted.published_at,
+    }, ensure_ascii=False), encoding="utf-8")
+    return str(path)
+
+async def process_job(job_id: str, store: JobStore):
+    job = await store.get_job(job_id)
+    if not job:
+        return
+
+    url = job["url"]
+
+    try:
+        await store.update_status(job_id, JobStatus.FETCHING, stage="fetching")
+        html = await fetch_html(url)
+        raw_html_path = await _save_raw_html(job_id, html)
+
+        await store.update_status(job_id, JobStatus.EXTRACTING, stage="extracting", raw_html_path=raw_html_path)
+        extracted = extract(html, url)
+        extracted_json_path = await _save_extracted(job_id, extracted)
+
+        if not extracted.content or len(extracted.content.strip()) < 50:
+            await store.update_status(job_id, JobStatus.NEEDS_REVIEW, stage="extracting", last_error="Content too short", extracted_json_path=extracted_json_path)
+            return
+
+        await store.update_status(job_id, JobStatus.AI_PROCESSING, stage="ai_processing", extracted_json_path=extracted_json_path)
+        client = KimiClient(api_key=settings.kimi_api_key, model=settings.kimi_model)
+
+        last_error = None
+        for attempt in range(settings.max_retry):
+            try:
+                ai_result = await client.process(extracted, url=url)
+                break
+            except Exception as e:
+                last_error = str(e)
+                await asyncio.sleep(2 ** attempt)
+        else:
+            ai_result = {
+                "title": extracted.title or url,
+                "category": "未分类",
+                "tags": [],
+                "summary": "",
+                "content_markdown": extracted.content,
+                "author": extracted.author,
+                "published_at": extracted.published_at,
+            }
+
+        await store.update_status(job_id, JobStatus.SAVING, stage="saving")
+        vault_path = await save_clip(job_id, url, ai_result, extracted, settings.vault_path)
+
+        await store.update_status(job_id, JobStatus.DONE, stage="done", vault_path=str(vault_path))
+
+    except Exception as e:
+        retry_count = job["retry_count"] + 1
+        if retry_count < job["max_retries"]:
+            await store.update_status(job_id, JobStatus.PENDING, stage="pending", retry_count=retry_count, last_error=str(e))
+        else:
+            await store.update_status(job_id, JobStatus.FAILED, stage="failed", retry_count=retry_count, last_error=str(e))
diff --git a/tests/test_worker.py b/tests/test_worker.py
new file mode 100644
index 0000000..248eaf1
--- /dev/null
+++ b/tests/test_worker.py
@@ -0,0 +1,23 @@
+import pytest
+from src.core.storage import JobStore
+from src.worker.worker import process_job
+from src.config import Settings
+
+async def test_process_job_success(tmp_path, monkeypatch, respx_mock):
+    db_path = tmp_path / "test.db"
+    store = JobStore(str(db_path))
+    await store.init()
+
+    respx_mock.get("https://example.com").respond(200, text="<html><head><title>T</title></head><body><p>Hello world, this is a longer content that should pass the 50 character minimum threshold for processing. It needs to be at least fifty characters long to avoid the needs_review status.</p></body></html>")
+    respx_mock.post("https://api.moonshot.cn/v1/chat/completions").respond(json={
+        "choices": [{"message": {"content": '{"title":"T","category":"未分类","tags":[],"summary":"S","content_markdown":"Hello","author":"","published_at":""}'}}]
+    })
+
+    monkeypatch.setenv("VAULT_PATH", str(tmp_path / "vault"))
+    monkeypatch.setenv("KIMI_API_KEY", "test-kimi-key")
+    monkeypatch.setenv("API_KEYS", "test-key-1,test-key-2")
+    job = await store.create_job("https://example.com")
+    await process_job(job["id"], store)
+    updated = await store.get_job(job["id"])
+    assert updated["status"] == "done"
+    assert updated["vault_path"] is not None
.superpowers/sdd/review-38e5177-226d13b.md
