from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from src.config import Settings
from src.core.storage import JobStore
from src.core.models import JobStatus

settings = Settings()
store = JobStore(settings.database_path)
templates = Jinja2Templates(directory="src/web/templates")

router = APIRouter(prefix="/web")


@router.on_event("startup")
async def startup():
    await store.init()


@router.get("/", response_class=HTMLResponse)
async def list_clips(request: Request):
    jobs = await store.list_jobs(limit=100)
    return templates.TemplateResponse(
        request=request, name="list.html", context={"jobs": jobs}
    )


@router.get("/clips/{job_id}", response_class=HTMLResponse)
async def clip_detail(request: Request, job_id: str):
    job = await store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Not found")
    return templates.TemplateResponse(
        request=request, name="detail.html", context={"job": job}
    )


@router.get("/failed", response_class=HTMLResponse)
async def failed_clips(request: Request):
    jobs = await store.list_failed_jobs()
    return templates.TemplateResponse(
        request=request, name="failed.html", context={"jobs": jobs}
    )


@router.get("/queue", response_class=HTMLResponse)
async def queue_status(request: Request):
    pending = await store.list_jobs(status=JobStatus.PENDING)
    fetching = await store.list_jobs(status=JobStatus.FETCHING)
    return templates.TemplateResponse(
        request=request, name="queue.html", context={"pending": len(pending), "fetching": len(fetching)}
    )
