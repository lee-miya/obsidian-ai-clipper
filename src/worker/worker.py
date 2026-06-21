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
            except asyncio.CancelledError:
                raise
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
            last_error = last_error or "AI processing failed after all retries"

        await store.update_status(job_id, JobStatus.SAVING, stage="saving")
        vault_path = await save_clip(job_id, url, ai_result, extracted, settings.vault_path)

        if last_error:
            await store.update_status(job_id, JobStatus.NEEDS_REVIEW, stage="done", vault_path=str(vault_path), last_error=last_error)
        else:
            await store.update_status(job_id, JobStatus.DONE, stage="done", vault_path=str(vault_path))

    except asyncio.CancelledError:
        raise
    except Exception as e:
        retry_count = job["retry_count"] + 1
        if retry_count < job["max_retries"]:
            await store.update_status(job_id, JobStatus.PENDING, stage="pending", retry_count=retry_count, last_error=str(e))
        else:
            await store.update_status(job_id, JobStatus.FAILED, stage="failed", retry_count=retry_count, last_error=str(e))
