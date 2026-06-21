import asyncio

from fastapi import APIRouter, Depends, HTTPException

from src.api.deps import require_api_key
from src.config import Settings
from src.core.models import ClipRequest, ClipResponse, JobResponse
from src.core.storage import JobStore
from src.utils.url import validate_public_url
from src.worker.worker import process_job

settings = Settings()
store = JobStore(settings.database_path)

router = APIRouter(prefix="/api")


@router.on_event("startup")
async def startup():
    await store.init()


@router.post("/clip", response_model=ClipResponse, status_code=202)
async def create_clip(request: ClipRequest, api_key: str = Depends(require_api_key)):
    try:
        validate_public_url(str(request.url))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    existing = await store.list_jobs(limit=1)
    for job in existing:
        if job["url"] == str(request.url):
            raise HTTPException(status_code=409, detail="URL already clipped recently")

    job = await store.create_job(str(request.url))
    asyncio.create_task(process_job(job["id"], store))
    return ClipResponse(job_id=job["id"], status=job["status"])


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str, api_key: str = Depends(require_api_key)):
    job = await store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse(**job)
