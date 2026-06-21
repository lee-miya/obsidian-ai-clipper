# Task 10 Brief

Source plan: docs/superpowers/plans/2026-06-21-obsidian-ai-clipper-plan.md

## Task 10: FastAPI API Routes

**Files:**
- Modify: `src/main.py`
- Create: `src/api/deps.py`
- Create: `src/api/routes.py`
- Test: `tests/test_api.py`

**Interfaces:**
- Consumes: `verify_api_key`, `validate_public_url`, `JobStore`, `process_job`.
- Produces: `POST /api/clip`, `GET /api/jobs/{job_id}`, `GET /health`.

- [ ] **Step 1: Write failing tests**

```python
import pytest
from fastapi.testclient import TestClient
from src.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200

def test_clip_requires_auth(client):
    response = client.post("/api/clip", json={"url": "https://example.com"})
    assert response.status_code == 401
```

- [ ] **Step 2: Implement `src/api/deps.py`**

```python
from fastapi import Header, HTTPException
from src.config import Settings
from src.core.security import verify_api_key

settings = Settings()

async def require_api_key(authorization: str | None = Header(None)) -> str:
    try:
        return verify_api_key(authorization, settings.api_keys)
    except ValueError:
        raise HTTPException(status_code=401, detail="Unauthorized")
```

- [ ] **Step 3: Implement `src/api/routes.py`**

```python
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from src.api.deps import require_api_key
from src.core.models import ClipRequest, ClipResponse, JobResponse
from src.core.storage import JobStore
from src.utils.url import validate_public_url
from src.worker.worker import process_job
from src.config import Settings

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
```

- [ ] **Step 4: Implement `src/main.py`**

```python
from fastapi import FastAPI
from src.api.routes import router as api_router

app = FastAPI(title="Obsidian AI Clipper")
app.include_router(api_router)

@app.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 5: Run API tests**

Run: `pytest tests/test_api.py -v`  
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/main.py src/api/ tests/test_api.py
git commit -m "feat: add FastAPI clip endpoints"
```

---

