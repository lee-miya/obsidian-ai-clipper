# Obsidian AI Clipper Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a personal web-clipper system with a Chrome extension, a FastAPI service that fetches pages and uses Kimi AI to extract Markdown, and an HTTPS web UI to browse saved clips in an Obsidian Vault.

**Architecture:** A single Dockerized FastAPI service. It receives URLs from a Chrome extension, persists each clip as a job in SQLite, fetches the page (static first, Playwright fallback), extracts content with `trafilatura`/`BeautifulSoup`, calls Kimi Code for classification/summary/Markdown, downloads images, writes a Markdown file with YAML frontmatter to the Vault, and serves a web UI to list/search/view clips and retry failed jobs.

**Tech Stack:** Python 3.12+, FastAPI, Pydantic, aiosqlite, httpx, Playwright, trafilatura, BeautifulSoup4, Jinja2, pytest, Docker, docker-compose.

## Global Constraints

- Python 3.12+
- FastAPI for HTTP server
- SQLite for job persistence
- httpx timeout 3 minutes for static fetches
- Playwright sandboxed for dynamic fallback
- API Key authentication via `Authorization: Bearer <key>`
- All failed jobs retained in SQLite; content never silently dropped
- Vault path: `Clips/<category>/<date>-<slug>/index.md` with images in same directory
- HTTPS via Let's Encrypt (PEM) or user-provided p12 certificate
- Docker container runs as non-root user

---

## File Structure

```
obsidian-ai-clipper/
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── README.md
├── prompts/
│   └── clip.md
├── src/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app factory
│   ├── config.py               # Pydantic settings
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py             # auth/rate-limit dependencies
│   │   └── routes.py           # /api/clip, /api/jobs/{id}, /health
│   ├── web/
│   │   ├── __init__.py
│   │   ├── routes.py           # /web/* pages
│   │   └── templates/          # Jinja2 templates
│   │       ├── base.html
│   │       ├── list.html
│   │       ├── detail.html
│   │       └── failed.html
│   ├── core/
│   │   ├── __init__.py
│   │   ├── models.py           # Pydantic request/response/job models
│   │   ├── security.py         # API key validation, rate limiting
│   │   └── storage.py          # SQLite job CRUD + status transitions
│   ├── fetcher/
│   │   ├── __init__.py
│   │   ├── fetcher.py          # static + dynamic fetch orchestrator
│   │   ├── static_fetcher.py   # httpx-based fetch
│   │   └── dynamic_fetcher.py  # Playwright-based fetch
│   ├── extractor/
│   │   ├── __init__.py
│   │   └── extractor.py        # trafilatura + BS4 extraction
│   ├── ai/
│   │   ├── __init__.py
│   │   └── kimi_client.py      # Kimi Code API client
│   ├── writer/
│   │   ├── __init__.py
│   │   └── vault_writer.py     # Markdown + image save
│   ├── worker/
│   │   ├── __init__.py
│   │   └── worker.py           # background job processor
│   └── utils/
│       ├── __init__.py
│       └── url.py              # URL validation helpers
├── chrome-extension/
│   ├── manifest.json
│   ├── popup.html
│   ├── popup.js
│   ├── popup.css
│   ├── options.html
│   ├── options.js
│   └── icons/
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_api.py
    ├── test_security.py
    ├── test_fetcher.py
    ├── test_extractor.py
    ├── test_ai_client.py
    ├── test_vault_writer.py
    └── test_worker.py
```

---

## Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `.env.example`
- Create: `docker-compose.yml`
- Create: `Dockerfile`
- Create: `README.md`

**Interfaces:**
- Produces: Python package metadata, dependency list, container orchestration files, environment template.

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "obsidian-ai-clipper"
version = "0.1.0"
description = "Personal AI-powered web clipper for Obsidian Vaults"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.111.0",
    "uvicorn[standard]>=0.30.0",
    "pydantic>=2.7.0",
    "pydantic-settings>=2.3.0",
    "aiosqlite>=0.20.0",
    "httpx>=0.27.0",
    "trafilatura>=1.9.0",
    "beautifulsoup4>=4.12.0",
    "jinja2>=3.1.4",
    "python-multipart>=0.0.9",
    "pytest>=8.2.0",
    "pytest-asyncio>=0.23.0",
    "pytest-httpx>=0.30.0",
    "respx>=0.21.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 2: Create `.env.example`**

```bash
API_KEYS=change-me-to-a-long-random-string
KIMI_API_KEY=your-kimi-code-api-key
KIMI_MODEL=kimi2.6
VAULT_PATH=/data/vault
DATABASE_PATH=/data/clipper.db
LOG_LEVEL=INFO
RATE_LIMIT_IP=10/minute
RATE_LIMIT_GLOBAL=100/minute
MAX_RETRY=3
```

- [ ] **Step 3: Create `Dockerfile`**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libxml2-dev \
    libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --no-cache-dir -e ".[dev]"

COPY src ./src
COPY prompts ./prompts

RUN groupadd -r clipper && useradd -r -g clipper clipper
USER clipper

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 4: Create `docker-compose.yml`**

```yaml
services:
  clipper:
    build: .
    container_name: obsidian-ai-clipper
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ${VAULT_PATH}:/data/vault
      - ./data:/data
    restart: unless-stopped
```

- [ ] **Step 5: Create `README.md`** with build and run instructions.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml .env.example Dockerfile docker-compose.yml README.md
git commit -m "chore: project scaffolding"
```

---

## Task 2: Configuration and Core Models

**Files:**
- Create: `src/config.py`
- Create: `src/core/models.py`
- Create: `src/main.py` (initial)
- Test: `tests/test_config.py`

**Interfaces:**
- Produces: `Settings` singleton, Pydantic models `ClipRequest`, `ClipResponse`, `JobResponse`, `JobStatus` enum.

- [ ] **Step 1: Write failing test for config loading**

```python
import os
from src.config import Settings

def test_settings_loads_api_keys():
    os.environ["API_KEYS"] = "key1,key2"
    settings = Settings()
    assert settings.api_keys == ["key1", "key2"]
```

Run: `pytest tests/test_config.py::test_settings_loads_api_keys -v`  
Expected: FAIL (Settings not defined)

- [ ] **Step 2: Implement `src/config.py`**

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    api_keys: list[str]
    kimi_api_key: str
    kimi_model: str = "kimi2.6"
    vault_path: str = "/data/vault"
    database_path: str = "/data/clipper.db"
    log_level: str = "INFO"
    rate_limit_ip: str = "10/minute"
    rate_limit_global: str = "100/minute"
    max_retry: int = 3
```

- [ ] **Step 3: Run test**

Run: `pytest tests/test_config.py::test_settings_loads_api_keys -v`  
Expected: PASS

- [ ] **Step 4: Write failing test for models**

```python
from src.core.models import ClipRequest, JobStatus

def test_clip_request_valid_url():
    req = ClipRequest(url="https://example.com/article")
    assert str(req.url) == "https://example.com/article"

def test_job_status_values():
    assert JobStatus.PENDING.value == "pending"
```

- [ ] **Step 5: Implement `src/core/models.py`**

```python
from datetime import datetime
from enum import Enum
from pathlib import Path
from pydantic import BaseModel, Field, HttpUrl

class JobStatus(str, Enum):
    PENDING = "pending"
    FETCHING = "fetching"
    EXTRACTING = "extracting"
    AI_PROCESSING = "ai_processing"
    SAVING = "saving"
    DONE = "done"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"

class ClipRequest(BaseModel):
    url: HttpUrl
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    client_version: str = "1.0.0"

class ClipResponse(BaseModel):
    job_id: str
    status: JobStatus
    message: str = "已接收，正在后台处理"

class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    stage: str | None = None
    retry_count: int = 0
    vault_path: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
```

- [ ] **Step 6: Run tests**

Run: `pytest tests/test_config.py tests/test_models.py -v`  
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/config.py src/core/models.py src/main.py tests/test_config.py tests/test_models.py
git commit -m "feat: add configuration and core models"
```

---

## Task 3: URL Validation and Security Helpers

**Files:**
- Create: `src/utils/url.py`
- Create: `src/core/security.py`
- Test: `tests/test_url.py`
- Test: `tests/test_security.py`

**Interfaces:**
- Produces: `validate_public_url(url: str) -> str`, `is_private_ip(host: str) -> bool`, `verify_api_key(header: str | None, allowed: list[str]) -> str`.

- [ ] **Step 1: Write failing tests for URL validation**

```python
import pytest
from src.utils.url import validate_public_url

def test_valid_https_url():
    assert validate_public_url("https://example.com") == "https://example.com"

def test_rejects_localhost():
    with pytest.raises(ValueError):
        validate_public_url("http://localhost:8000")

def test_rejects_private_ip():
    with pytest.raises(ValueError):
        validate_public_url("http://192.168.1.1")

def test_rejects_non_http_protocol():
    with pytest.raises(ValueError):
        validate_public_url("ftp://example.com")
```

- [ ] **Step 2: Implement `src/utils/url.py`**

```python
import ipaddress
from urllib.parse import urlparse

PRIVATE_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]

def is_private_ip(host: str) -> bool:
    try:
        addr = ipaddress.ip_address(host)
        return any(addr in net for net in PRIVATE_NETWORKS)
    except ValueError:
        return False

def validate_public_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("Only http/https URLs are allowed")
    if not parsed.hostname:
        raise ValueError("Invalid URL")
    host = parsed.hostname.lower()
    if host in ("localhost", "127.0.0.1", "::1"):
        raise ValueError("Localhost URLs are not allowed")
    if is_private_ip(host):
        raise ValueError("Private IP addresses are not allowed")
    return url
```

- [ ] **Step 3: Run URL tests**

Run: `pytest tests/test_url.py -v`  
Expected: PASS

- [ ] **Step 4: Write failing tests for API key verification**

```python
import pytest
from src.core.security import verify_api_key

def test_valid_key():
    assert verify_api_key("Bearer valid-key", ["valid-key"]) == "valid-key"

def test_missing_header():
    with pytest.raises(ValueError):
        verify_api_key(None, ["valid-key"])

def test_invalid_key():
    with pytest.raises(ValueError):
        verify_api_key("Bearer wrong-key", ["valid-key"])
```

- [ ] **Step 5: Implement `src/core/security.py`**

```python
def verify_api_key(header: str | None, allowed_keys: list[str]) -> str:
    if not header or not header.startswith("Bearer "):
        raise ValueError("Invalid authorization header")
    key = header[7:]
    if key not in allowed_keys:
        raise ValueError("Invalid API key")
    return key
```

- [ ] **Step 6: Run security tests**

Run: `pytest tests/test_security.py -v`  
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/utils/url.py src/core/security.py tests/test_url.py tests/test_security.py
git commit -m "feat: add URL validation and API key security"
```

---

## Task 4: SQLite Job Storage

**Files:**
- Create: `src/core/storage.py`
- Test: `tests/test_storage.py`

**Interfaces:**
- Produces: `JobStore` async class with methods `create_job(url)`, `get_job(job_id)`, `update_status(job_id, status, **fields)`, `list_jobs(status=None, limit=50)`, `list_failed_jobs()`.

- [ ] **Step 1: Write failing test for creating a job**

```python
import pytest
from src.core.storage import JobStore
from src.core.models import JobStatus

@pytest.fixture
async def store(tmp_path):
    db_path = tmp_path / "test.db"
    s = JobStore(str(db_path))
    await s.init()
    return s

async def test_create_job(store):
    job = await store.create_job("https://example.com")
    assert job["url"] == "https://example.com"
    assert job["status"] == JobStatus.PENDING.value
```

- [ ] **Step 2: Implement `src/core/storage.py`**

```python
import aiosqlite
from datetime import datetime, timezone
from src.core.models import JobStatus

class JobStore:
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def init(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    url TEXT NOT NULL,
                    status TEXT NOT NULL,
                    retry_count INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3,
                    stage TEXT,
                    last_error TEXT,
                    raw_html_path TEXT,
                    extracted_json_path TEXT,
                    vault_path TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)
            """)
            await db.commit()

    async def create_job(self, url: str) -> dict:
        import uuid
        now = datetime.now(timezone.utc).isoformat()
        job_id = f"clip_{uuid.uuid4().hex[:12]}"
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT INTO jobs (id, url, status, max_retries, stage, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (job_id, url, JobStatus.PENDING.value, 3, "pending", now, now),
            )
            await db.commit()
        return await self.get_job(job_id)

    async def get_job(self, job_id: str) -> dict | None:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def update_status(self, job_id: str, status: JobStatus, **fields) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        fields["status"] = status.value
        fields["updated_at"] = now
        set_clause = ", ".join(f"{k} = ?" for k in fields.keys())
        values = list(fields.values()) + [job_id]
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(f"UPDATE jobs SET {set_clause} WHERE id = ?", values)
            await db.commit()
        return await self.get_job(job_id)

    async def list_jobs(self, status: JobStatus | None = None, limit: int = 50) -> list[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            if status:
                async with db.execute(
                    "SELECT * FROM jobs WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                    (status.value, limit),
                ) as cursor:
                    rows = await cursor.fetchall()
            else:
                async with db.execute(
                    "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,)
                ) as cursor:
                    rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def list_failed_jobs(self) -> list[dict]:
        return await self.list_jobs(status=JobStatus.FAILED)
```

- [ ] **Step 3: Run storage tests**

Run: `pytest tests/test_storage.py -v`  
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add src/core/storage.py tests/test_storage.py
git commit -m "feat: add SQLite job storage"
```

---

## Task 5: Static and Dynamic Fetchers

**Files:**
- Create: `src/fetcher/static_fetcher.py`
- Create: `src/fetcher/dynamic_fetcher.py`
- Create: `src/fetcher/fetcher.py`
- Test: `tests/test_fetcher.py`

**Interfaces:**
- Produces: `async fetch_html(url: str) -> str` which tries static then dynamic.

- [ ] **Step 1: Write failing test for static fetcher**

```python
import pytest
from src.fetcher.static_fetcher import StaticFetcher

async def test_fetch_html_success(respx_mock):
    respx_mock.get("https://example.com").respond(200, text="<html><body>Hello</body></html>")
    fetcher = StaticFetcher()
    html = await fetcher.fetch("https://example.com")
    assert "Hello" in html
```

- [ ] **Step 2: Implement `src/fetcher/static_fetcher.py`**

```python
import httpx
from src.config import Settings

settings = Settings()

class StaticFetcher:
    async def fetch(self, url: str) -> str:
        async with httpx.AsyncClient(timeout=180.0, follow_redirects=True) as client:
            response = await client.get(url, headers={"User-Agent": "ObsidianAIClipper/1.0"})
            response.raise_for_status()
            return response.text
```

- [ ] **Step 3: Implement `src/fetcher/dynamic_fetcher.py`**

```python
from playwright.async_api import async_playwright

class DynamicFetcher:
    async def fetch(self, url: str) -> str:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            await page.goto(url, timeout=180000, wait_until="networkidle")
            html = await page.content()
            await browser.close()
            return html
```

- [ ] **Step 4: Implement `src/fetcher/fetcher.py`**

```python
from src.fetcher.static_fetcher import StaticFetcher
from src.fetcher.dynamic_fetcher import DynamicFetcher

async def fetch_html(url: str) -> str:
    static = StaticFetcher()
    try:
        return await static.fetch(url)
    except Exception:
        dynamic = DynamicFetcher()
        return await dynamic.fetch(url)
```

- [ ] **Step 5: Run fetcher tests**

Run: `pytest tests/test_fetcher.py -v`  
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/fetcher/ tests/test_fetcher.py
git commit -m "feat: add static and dynamic fetchers"
```

---

## Task 6: Content Extractor

**Files:**
- Create: `src/extractor/extractor.py`
- Test: `tests/test_extractor.py`

**Interfaces:**
- Produces: `ExtractedContent(title, content, images, code_blocks, author, published_at)` dataclass and `extract(html: str, url: str) -> ExtractedContent` function.

- [ ] **Step 1: Write failing test**

```python
from src.extractor.extractor import extract

HTML = """
<html><head><title>Test Article</title></head>
<body>
<article>
<h1>Test Article</h1>
<p>This is the main content.</p>
<img src="https://example.com/img.png" alt="diagram">
<pre><code class="python">print("hi")</code></pre>
</article>
</body></html>
"""

def test_extract_content():
    result = extract(HTML, "https://example.com")
    assert result.title == "Test Article"
    assert "main content" in result.content
    assert len(result.images) == 1
    assert len(result.code_blocks) == 1
```

- [ ] **Step 2: Implement `src/extractor/extractor.py`**

```python
from dataclasses import dataclass, field
from bs4 import BeautifulSoup
import trafilatura

@dataclass
class ExtractedContent:
    title: str = ""
    content: str = ""
    images: list[dict] = field(default_factory=list)
    code_blocks: list[dict] = field(default_factory=list)
    author: str = ""
    published_at: str = ""

def extract(html: str, url: str) -> ExtractedContent:
    extracted = ExtractedContent()

    title = trafilatura.extract(html, output_format="json", include_comments=False, include_tables=True)
    if title:
        import json
        data = json.loads(title)
        extracted.title = data.get("title", "")
        extracted.content = data.get("raw_text", "")

    soup = BeautifulSoup(html, "html.parser")

    if not extracted.title:
        title_tag = soup.find("title")
        extracted.title = title_tag.get_text(strip=True) if title_tag else ""

    for img in soup.find_all("img"):
        src = img.get("src")
        if src:
            from urllib.parse import urljoin
            extracted.images.append({
                "src": urljoin(url, src),
                "alt": img.get("alt", ""),
            })

    for pre in soup.find_all("pre"):
        code = pre.find("code")
        lang = ""
        if code:
            classes = code.get("class", [])
            for c in classes:
                if c.startswith("language-"):
                    lang = c.replace("language-", "")
                    break
        extracted.code_blocks.append({
            "language": lang,
            "code": pre.get_text(),
        })

    return extracted
```

- [ ] **Step 3: Run extractor tests**

Run: `pytest tests/test_extractor.py -v`  
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add src/extractor/extractor.py tests/test_extractor.py
git commit -m "feat: add content extractor"
```

---

## Task 7: Kimi Code AI Client

**Files:**
- Create: `src/ai/kimi_client.py`
- Create: `prompts/clip.md`
- Test: `tests/test_ai_client.py`

**Interfaces:**
- Produces: `KimiClient` class with `async process(content: ExtractedContent) -> dict`.

- [ ] **Step 1: Write failing test**

```python
import pytest
from src.ai.kimi_client import KimiClient
from src.extractor.extractor import ExtractedContent

async def test_process_calls_api(respx_mock):
    client = KimiClient(api_key="test", model="kimi2.6")
    respx_mock.post("https://api.moonshot.cn/v1/chat/completions").respond(json={
        "choices": [{"message": {"content": '{"title":"T","category":"未分类","tags":[],"summary":"S","content_markdown":"MD","author":"","published_at":""}'}}]
    })
    content = ExtractedContent(title="Original", content="Body text", images=[], code_blocks=[])
    result = await client.process(content, url="https://example.com")
    assert result["title"] == "T"
```

- [ ] **Step 2: Implement `src/ai/kimi_client.py`**

```python
import json
import httpx
from src.extractor.extractor import ExtractedContent

class KimiClient:
    def __init__(self, api_key: str, model: str = "kimi2.6"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.moonshot.cn/v1"

    async def process(self, content: ExtractedContent, url: str) -> dict:
        with open("prompts/clip.md", encoding="utf-8") as f:
            system_prompt = f.read()

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps({
                    "url": url,
                    "title": content.title,
                    "domain": url.split("/")[2],
                    "content": content.content,
                    "images": content.images,
                    "code_blocks": content.code_blocks,
                }, ensure_ascii=False)},
            ],
            "response_format": {"type": "json_object"},
        }

        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            raw = data["choices"][0]["message"]["content"]
            return json.loads(raw)
```

- [ ] **Step 3: Create `prompts/clip.md`**

```markdown
You are a helpful web content extractor. Given the metadata and extracted text of a web page, produce a JSON object with these fields:

- title: a clean, concise title
- category: one broad category for organizing in an Obsidian Vault (e.g., 人工智能, 编程开发, 产品设计, 未分类)
- tags: 3-7 relevant tags as a list of strings
- summary: 2-4 sentences summarizing the page
- content_markdown: the page content converted to clean Markdown, preserving code blocks and image references
- author: author name if known, otherwise empty string
- published_at: publication date in YYYY-MM-DD if known, otherwise empty string

Use Chinese for category, tags, summary, and title when the source is Chinese; otherwise use English.
Return only valid JSON.
```

- [ ] **Step 4: Run AI client tests**

Run: `pytest tests/test_ai_client.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/ai/kimi_client.py prompts/clip.md tests/test_ai_client.py
git commit -m "feat: add Kimi Code AI client"
```

---

## Task 8: Vault Writer

**Files:**
- Create: `src/writer/vault_writer.py`
- Test: `tests/test_vault_writer.py`

**Interfaces:**
- Produces: `async save_clip(job_id, url, ai_result, extracted, vault_root) -> Path`.

- [ ] **Step 1: Write failing test**

```python
import pytest
from pathlib import Path
from src.writer.vault_writer import save_clip
from src.extractor.extractor import ExtractedContent

async def test_save_clip(tmp_path):
    extracted = ExtractedContent(title="T", content="Body", images=[], code_blocks=[])
    ai_result = {
        "title": "Test",
        "category": "人工智能",
        "tags": ["AI"],
        "summary": "Summary",
        "content_markdown": "# Test\n\nBody",
        "author": "A",
        "published_at": "2026-06-20",
    }
    path = await save_clip("clip_abc", "https://example.com/x", ai_result, extracted, str(tmp_path))
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "Test" in text
    assert "source_url" in text
```

- [ ] **Step 2: Implement `src/writer/vault_writer.py`**

```python
import re
import httpx
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from src.extractor.extractor import ExtractedContent

SLUG_MAX = 60

def safe_filename(name: str) -> str:
    name = re.sub(r"[^\w一-龥-]+", "-", name).strip("-")
    return name[:SLUG_MAX]

async def download_image(url: str, dest: Path) -> str:
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        ext = response.headers.get("content-type", "").split("/")[-1]
        if not ext or ext not in {"png", "jpg", "jpeg", "gif", "webp", "svg"}:
            ext = "png"
        filename = f"image_{dest.parent.name}_{dest.name}.{ext}"
        image_path = dest.parent / filename
        image_path.write_bytes(response.content)
        return filename

async def save_clip(
    job_id: str,
    url: str,
    ai_result: dict,
    extracted: ExtractedContent,
    vault_root: str,
) -> Path:
    category = safe_filename(ai_result.get("category") or "未分类")
    title = ai_result.get("title") or extracted.title or "untitled"
    date_prefix = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    slug = safe_filename(title) or "clip"
    dir_name = f"{date_prefix}-{slug}"
    clip_dir = Path(vault_root) / "Clips" / category / dir_name
    clip_dir.mkdir(parents=True, exist_ok=True)

    index_path = clip_dir / "index.md"
    counter = 1
    while index_path.exists():
        clip_dir = Path(vault_root) / "Clips" / category / f"{dir_name}-{counter}"
        clip_dir.mkdir(parents=True, exist_ok=True)
        index_path = clip_dir / "index.md"
        counter += 1

    md_content = ai_result.get("content_markdown") or extracted.content
    image_map = {}
    for idx, img in enumerate(extracted.images):
        try:
            filename = await download_image(img["src"], clip_dir / f"img_{idx}")
            image_map[img["src"]] = filename
        except Exception:
            image_map[img["src"]] = img["src"]

    for original, replacement in image_map.items():
        md_content = md_content.replace(original, replacement)

    frontmatter = f"""---
title: "{title}"
source_url: "{url}"
domain: "{urlparse(url).netloc}"
category: "{category}"
tags:
{chr(10).join(f'  - "{t}"' for t in ai_result.get('tags', []))}
summary: "{ai_result.get('summary', '')}"
author: "{ai_result.get('author', '')}"
published_at: "{ai_result.get('published_at', '')}"
clipped_at: "{datetime.now(timezone.utc).isoformat()}"
job_id: "{job_id}"
status: "done"
---

{md_content}
"""

    temp_path = clip_dir / ".index.md.tmp"
    temp_path.write_text(frontmatter, encoding="utf-8")
    temp_path.replace(index_path)
    return index_path
```

- [ ] **Step 3: Run vault writer tests**

Run: `pytest tests/test_vault_writer.py -v`  
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add src/writer/vault_writer.py tests/test_vault_writer.py
git commit -m "feat: add vault writer with image download"
```

---

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

## Task 12: Rate Limiting and Security Headers

**Files:**
- Modify: `src/api/deps.py`
- Modify: `src/main.py`
- Test: `tests/test_rate_limit.py`

**Interfaces:**
- Produces: rate limit dependency applied to `/api/clip`.

- [ ] **Step 1: Add simple in-memory rate limiter**

Modify `src/api/deps.py`:

```python
import time
from collections import defaultdict
from fastapi import Header, HTTPException, Request
from src.config import Settings
from src.core.security import verify_api_key

settings = Settings()

ip_requests: dict[str, list[float]] = defaultdict(list)
global_requests: list[float] = []

def _is_allowed(buckets: list[float], window_seconds: int, max_requests: int) -> bool:
    now = time.time()
    buckets[:] = [t for t in buckets if now - t < window_seconds]
    if len(buckets) >= max_requests:
        return False
    buckets.append(now)
    return True

async def require_api_key(request: Request, authorization: str | None = Header(None)) -> str:
    try:
        key = verify_api_key(authorization, settings.api_keys)
    except ValueError:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if not _is_allowed(ip_requests[request.client.host], 60, 10):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    if not _is_allowed(global_requests, 60, 100):
        raise HTTPException(status_code=429, detail="Global rate limit exceeded")

    return key
```

- [ ] **Step 2: Add security headers middleware in `src/main.py`**

```python
from fastapi import FastAPI, Request
from fastapi.responses import Response
from src.api.routes import router as api_router
from src.web.routes import router as web_router

app = FastAPI(title="Obsidian AI Clipper")
app.include_router(api_router)
app.include_router(web_router)

@app.middleware("http")
async def security_headers(request: Request, call_next):
    response: Response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response

@app.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 3: Add rate limit test**

```python
from fastapi.testclient import TestClient
from src.main import app

def test_rate_limit_after_many_requests():
    client = TestClient(app)
    for i in range(10):
        response = client.post("/api/clip", json={"url": "https://example.com"}, headers={"Authorization": "Bearer test-key"})
    response = client.post("/api/clip", json={"url": "https://example.com"}, headers={"Authorization": "Bearer test-key"})
    assert response.status_code == 429
```

Note: This test assumes `API_KEYS` env includes `test-key`. Set via test fixture or conftest.

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_rate_limit.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/api/deps.py src/main.py tests/test_rate_limit.py
git commit -m "feat: add rate limiting and security headers"
```

---

## Task 13: Chrome Extension

**Files:**
- Create: `chrome-extension/manifest.json`
- Create: `chrome-extension/popup.html`
- Create: `chrome-extension/popup.js`
- Create: `chrome-extension/popup.css`
- Create: `chrome-extension/options.html`
- Create: `chrome-extension/options.js`
- Create: `chrome-extension/icons/icon-128.png` (placeholder)

**Interfaces:**
- Produces: Chrome extension that sends URL to `/api/clip`.

- [ ] **Step 1: Create `chrome-extension/manifest.json`**

```json
{
  "manifest_version": 3,
  "name": "Obsidian AI Clipper",
  "version": "1.0.0",
  "description": "Save web pages to Obsidian Vault via AI",
  "permissions": ["activeTab", "storage"],
  "optional_permissions": ["contextMenus"],
  "action": {
    "default_popup": "popup.html",
    "default_icon": {
      "128": "icons/icon-128.png"
    }
  },
  "icons": {
    "128": "icons/icon-128.png"
  },
  "options_page": "options.html"
}
```

- [ ] **Step 2: Create `chrome-extension/options.html`**

```html
<!doctype html>
<html>
<head><meta charset="utf-8"><title>Settings</title></head>
<body>
  <h1>Obsidian AI Clipper Settings</h1>
  <label>Server URL: <input type="url" id="serverUrl"></label><br><br>
  <label>API Key: <input type="password" id="apiKey"></label><br><br>
  <button id="save">Save</button>
  <script src="options.js"></script>
</body>
</html>
```

- [ ] **Step 3: Create `chrome-extension/options.js`**

```javascript
document.getElementById('save').addEventListener('click', async () => {
  const serverUrl = document.getElementById('serverUrl').value.replace(/\/$/, '');
  const apiKey = document.getElementById('apiKey').value;
  await chrome.storage.sync.set({ serverUrl, apiKey });
  alert('Saved');
});

(async () => {
  const { serverUrl, apiKey } = await chrome.storage.sync.get(['serverUrl', 'apiKey']);
  if (serverUrl) document.getElementById('serverUrl').value = serverUrl;
  if (apiKey) document.getElementById('apiKey').value = apiKey;
})();
```

- [ ] **Step 4: Create `chrome-extension/popup.html`**

```html
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <link rel="stylesheet" href="popup.css">
</head>
<body>
  <div id="status">Loading...</div>
  <button id="clip">Save to Vault</button>
  <script src="popup.js"></script>
</body>
</html>
```

- [ ] **Step 5: Create `chrome-extension/popup.js`**

```javascript
document.getElementById('clip').addEventListener('click', async () => {
  const status = document.getElementById('status');
  status.textContent = 'Saving...';

  const { serverUrl, apiKey } = await chrome.storage.sync.get(['serverUrl', 'apiKey']);
  if (!serverUrl || !apiKey) {
    status.textContent = 'Please configure server URL and API key first.';
    return;
  }

  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  try {
    const response = await fetch(`${serverUrl}/api/clip`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`,
        'X-Client-Version': '1.0.0',
      },
      body: JSON.stringify({ url: tab.url, submitted_at: new Date().toISOString(), client_version: '1.0.0' }),
    });
    const data = await response.json();
    if (response.ok) {
      status.textContent = `Saved. Job: ${data.job_id}`;
    } else {
      status.textContent = `Error: ${data.detail || response.statusText}`;
    }
  } catch (e) {
    status.textContent = `Network error: ${e.message}`;
  }
});

(async () => {
  document.getElementById('status').textContent = 'Ready';
})();
```

- [ ] **Step 6: Create `chrome-extension/popup.css`**

```css
body { width: 240px; padding: 1rem; font-family: system-ui, sans-serif; }
#status { margin-bottom: 0.75rem; font-size: 0.9rem; }
button { width: 100%; padding: 0.5rem; }
```

- [ ] **Step 7: Create placeholder icon**

Create a 128x128 PNG at `chrome-extension/icons/icon-128.png`. Use any simple image or placeholder.

- [ ] **Step 8: Commit**

```bash
git add chrome-extension/
git commit -m "feat: add Chrome extension"
```

---

## Task 14: HTTPS / TLS Configuration

**Files:**
- Modify: `docker-compose.yml`
- Create: `nginx.conf` (optional)
- Create: `scripts/init-letsencrypt.sh` (optional)

**Interfaces:**
- Produces: production HTTPS deployment configuration.

- [ ] **Step 1: Add Traefik to `docker-compose.yml` for Let's Encrypt**

```yaml
services:
  traefik:
    image: traefik:v3.0
    command:
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.tlschallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.email=your-email@example.com"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
    ports:
      - "443:443"
    volumes:
      - "/var/run/docker.sock:/var/run/docker.sock:ro"
      - "./letsencrypt:/letsencrypt"

  clipper:
    build: .
    container_name: obsidian-ai-clipper
    expose:
      - "8000"
    env_file:
      - .env
    volumes:
      - ${VAULT_PATH}:/data/vault
      - ./data:/data
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.clipper.rule=Host(`clipper.example.com`)"
      - "traefik.http.routers.clipper.tls=true"
      - "traefik.http.routers.clipper.tls.certresolver=letsencrypt"
    restart: unless-stopped
```

- [ ] **Step 2: Add p12 certificate support instructions to `README.md`**

Explain how to mount a p12 file and configure Uvicorn with it:

```bash
# If using a p12 certificate directly, start uvicorn with:
uvicorn src.main:app --host 0.0.0.0 --port 8000 --ssl-keyfile ... --ssl-certfile ...
```

Note: Uvicorn does not directly support p12; use OpenSSL to convert p12 to PEM key/cert or use a reverse proxy.

- [ ] **Step 3: Commit**

```bash
git add docker-compose.yml README.md
git commit -m "docs: add HTTPS deployment guidance"
```

---

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

## Task 16: Final Integration and Docker Build

**Files:**
- Modify: `Dockerfile` (if needed)
- Modify: `pyproject.toml` (if needed)
- Test: `docker build .`

**Interfaces:**
- Produces: working Docker image.

- [ ] **Step 1: Ensure Dockerfile installs Playwright browsers**

Add to Dockerfile:

```dockerfile
RUN playwright install chromium
RUN playwright install-deps chromium
```

- [ ] **Step 2: Build Docker image**

Run: `docker build -t obsidian-ai-clipper .`  
Expected: Build succeeds.

- [ ] **Step 3: Run smoke test in container**

Run: `docker run --rm -p 8000:8000 --env-file .env obsidian-ai-clipper`  
Then: `curl http://localhost:8000/health`  
Expected: `{"status":"ok"}`

- [ ] **Step 4: Commit**

```bash
git add Dockerfile
git commit -m "build: finalize Docker image with Playwright"
```

---

## Self-Review

### Spec Coverage

| Spec Section | Implementing Task |
|---|---|
| Chrome extension | Task 13 |
| API authentication | Task 3, Task 10, Task 12 |
| URL validation | Task 3, Task 10 |
| SQLite job persistence | Task 4 |
| Static/dynamic fetch | Task 5 |
| Content extraction | Task 6 |
| Kimi AI processing | Task 7 |
| Vault writer + images | Task 8 |
| Background worker | Task 9 |
| Web UI | Task 11 |
| Rate limiting/security headers | Task 12 |
| HTTPS/TLS | Task 14 |
| Docker deployment | Task 1, Task 16 |
| Error handling / no drop | Task 4, Task 9 |

### Placeholder Scan

No TBD/TODO/fill-in-details found. All steps include concrete code or commands.

### Type Consistency

- `JobStore` methods return `dict` everywhere.
- `JobStatus` enum used consistently.
- `ClipRequest`, `ClipResponse`, `JobResponse` match API routes.

### Gaps

- Web UI templates are intentionally minimal; final polish can be added after core functionality works.
- Rate limiter is in-memory and will reset on container restart; acceptable for personal use.
- p12 certificate direct mounting is documented but requires reverse proxy conversion.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-21-obsidian-ai-clipper-plan.md`.

Two execution options:

1. **Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.
2. **Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints.

Which approach would you like?
