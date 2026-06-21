# Task 11 Brief

Source plan: docs/superpowers/plans/2026-06-21-obsidian-ai-clipper-plan.md

## Task 11: Web UI Routes and Templates

**Files:**
- Create: `src/web/routes.py`
- Create: `src/web/templates/base.html`
- Create: `src/web/templates/list.html`
- Create: `src/web/templates/detail.html`
- Create: `src/web/templates/failed.html`
- Modify: `src/main.py`
- Test: `tests/test_web.py`

**Interfaces:**
- Consumes: `JobStore`.
- Produces: `/web`, `/web/clips/{id}`, `/web/failed`, `/web/queue`.

- [ ] **Step 1: Write failing test**

```python
from fastapi.testclient import TestClient
from src.main import app

def test_web_list():
    client = TestClient(app)
    response = client.get("/web")
    assert response.status_code == 200
```

- [ ] **Step 2: Create templates**

`src/web/templates/base.html`:

```html
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% block title %}Obsidian AI Clipper{% endblock %}</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 900px; margin: 2rem auto; padding: 0 1rem; }
    nav a { margin-right: 1rem; }
    table { width: 100%; border-collapse: collapse; margin-top: 1rem; }
    th, td { border: 1px solid #ccc; padding: 0.5rem; text-align: left; }
    .tag { background: #eee; padding: 0.1rem 0.4rem; border-radius: 0.2rem; margin-right: 0.3rem; font-size: 0.85rem; }
  </style>
</head>
<body>
  <nav>
    <a href="/web">剪藏列表</a>
    <a href="/web/failed">失败任务</a>
    <a href="/web/queue">队列</a>
  </nav>
  {% block content %}{% endblock %}
</body>
</html>
```

`src/web/templates/list.html`:

```html
{% extends "base.html" %}
{% block content %}
<h1>剪藏列表</h1>
<table>
  <tr><th>标题</th><th>分类</th><th>状态</th><th>时间</th></tr>
  {% for job in jobs %}
  <tr>
    <td><a href="/web/clips/{{ job.id }}">{{ job.url }}</a></td>
    <td>{{ job.status }}</td>
    <td>{{ job.created_at }}</td>
  </tr>
  {% endfor %}
</table>
{% endblock %}
```

`src/web/templates/detail.html`, `failed.html` 类似，按需提供状态和重试按钮。

- [ ] **Step 3: Implement `src/web/routes.py`**

```python
from fastapi import APIRouter, Request, HTTPException
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

@router.get("/")
async def list_clips(request: Request):
    jobs = await store.list_jobs(limit=100)
    return templates.TemplateResponse("list.html", {"request": request, "jobs": jobs})

@router.get("/clips/{job_id}")
async def clip_detail(request: Request, job_id: str):
    job = await store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Not found")
    return templates.TemplateResponse("detail.html", {"request": request, "job": job})

@router.get("/failed")
async def failed_clips(request: Request):
    jobs = await store.list_failed_jobs()
    return templates.TemplateResponse("failed.html", {"request": request, "jobs": jobs})

@router.get("/queue")
async def queue_status(request: Request):
    pending = await store.list_jobs(status=JobStatus.PENDING)
    fetching = await store.list_jobs(status=JobStatus.FETCHING)
    return templates.TemplateResponse("queue.html", {"request": request, "pending": len(pending), "fetching": len(fetching)})
```

- [ ] **Step 4: Wire Web UI into `src/main.py`**

```python
from fastapi import FastAPI
from src.api.routes import router as api_router
from src.web.routes import router as web_router

app = FastAPI(title="Obsidian AI Clipper")
app.include_router(api_router)
app.include_router(web_router)

@app.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 5: Run web tests**

Run: `pytest tests/test_web.py -v`  
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/web/ src/main.py tests/test_web.py
git commit -m "feat: add web UI for browsing clips"
```

---

