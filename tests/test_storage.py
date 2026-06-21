import pytest
import os
from src.core.storage import JobStore
from src.core.models import JobStatus

@pytest.fixture
async def store(tmp_path):
    os.environ["KIMI_API_KEY"] = "test-key"
    db_path = tmp_path / "test.db"
    s = JobStore(str(db_path))
    await s.init()
    return s

async def test_create_job(store):
    job = await store.create_job("https://example.com")
    assert job["url"] == "https://example.com"
    assert job["status"] == JobStatus.PENDING.value

async def test_get_job(store):
    job = await store.create_job("https://example.com")
    fetched = await store.get_job(job["id"])
    assert fetched["url"] == "https://example.com"

async def test_update_status(store):
    job = await store.create_job("https://example.com")
    updated = await store.update_status(job["id"], JobStatus.FETCHING, stage="fetching")
    assert updated["status"] == JobStatus.FETCHING.value
    assert updated["stage"] == "fetching"

async def test_list_jobs(store):
    await store.create_job("https://example1.com")
    await store.create_job("https://example2.com")
    jobs = await store.list_jobs()
    assert len(jobs) == 2

async def test_list_jobs_by_status(store):
    job1 = await store.create_job("https://example1.com")
    await store.create_job("https://example2.com")
    await store.update_status(job1["id"], JobStatus.FAILED)
    failed = await store.list_jobs(status=JobStatus.FAILED)
    assert len(failed) == 1

async def test_list_failed_jobs(store):
    job1 = await store.create_job("https://example1.com")
    await store.create_job("https://example2.com")
    await store.update_status(job1["id"], JobStatus.FAILED)
    failed = await store.list_failed_jobs()
    assert len(failed) == 1
    assert failed[0]["status"] == JobStatus.FAILED.value
