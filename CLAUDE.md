# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Sync dependencies (run after any dependency change)
uv sync --group dev

# Run all tests
uv run pytest

# Run a single test file
uv run pytest tests/test_worker.py -v

# Run a single test
uv run pytest tests/test_worker.py::test_process_job_success -v

# Run the dev server
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000

# Build and run with Docker
docker compose up --build
```

Always use `uv run` for Python commands — never use system `python` or `pip`.

## Architecture

A monolithic FastAPI service that receives URLs from a Chrome extension, fetches web pages, extracts content, processes it with Kimi AI, and saves Markdown to an Obsidian Vault with YAML frontmatter.

**Pipeline (the critical path):**
```
Extension POST /api/clip → Auth + rate limit → validate_public_url → persist to SQLite
→ background asyncio task: fetch_html (httpx → Playwright fallback) → trafilatura+BS4 extract
→ KimiClient.process (Kimi Code API: api.kimi.com/coding/v1) → save_clip (Markdown + YAML frontmatter + image download)
→ Vault path: Clips/<category>/<date>-<slug>/index.md
```

## Service

- **`src/config.py`** — `Settings` (pydantic-settings). Comma-separated `API_KEYS` parsed via custom `CommaSeparatedEnvSource`. Fields default to empty so tests can construct without `.env`.
- **`src/main.py`** — FastAPI app, mounts `api_router` + `web_router`, adds security headers middleware.
- **`src/core/models.py`** — `JobStatus` enum, `ClipRequest`/`ClipResponse`/`JobResponse` (Pydantic). `JobResponse` allows extras for SQLite dict passthrough.
- **`src/core/storage.py`** — `JobStore` (async SQLite via `aiosqlite`). CRUD, index on status. No delete — failed jobs persist.
- **`src/core/security.py`** — `verify_api_key()` checks `Bearer <key>`.

## API

- **`src/api/deps.py`** — `require_api_key` dependency: verifies Bearer token, then rolling-window rate limits (IP 10/60s, global 100/60s). In-memory, resets on restart.
- **`src/api/routes.py`** — `POST /api/clip` (202 + job_id, spawns `asyncio.create_task`), `GET /api/jobs/{id}`.
- **`src/utils/url.py`** — `validate_public_url()` rejects non-http/https, localhost, private IPs (IPv4+IPv6).

## Processing Pipeline

- **`src/fetcher/`** — `fetch_html()` tries `StaticFetcher` (httpx, 180s), falls back to `DynamicFetcher` (Playwright Chromium) on httpx errors only.
- **`src/extractor/extractor.py`** — `extract()` uses trafilatura (body) + BeautifulSoup (images, code blocks, title fallback). Returns `ExtractedContent` dataclass.
- **`src/ai/kimi_client.py`** — `KimiClient.process()` calls `api.kimi.com/coding/v1`, model `kimi-for-coding`. No `response_format`. Retries HTTP errors 3× with exponential backoff, strips markdown fences from JSON responses. Raises `KimiAPIError` on terminal failure.
- **`src/writer/vault_writer.py`** — `save_clip()` generates YAML frontmatter via `yaml.safe_dump`, downloads images to clip dir, atomic write (tmp + rename), collision handling.
- **`src/worker/worker.py`** — `process_job()` orchestrates the full pipeline. AI exhaustion → fallback content saved as `needs_review`. `CancelledError` re-raised at both retry and outer levels. Fatal errors → retry (pending) or FAILED.

## Web UI

- **`src/web/routes.py`** — Jinja2 pages: `/web` (list), `/web/clips/{id}` (detail), `/web/failed`, `/web/queue`.
- **`src/web/templates/`** — `base.html` (layout with nav + CSS variables), `list.html`, `detail.html`, `failed.html`, `queue.html`.

## Chrome Extension

- **`chrome-extension/`** — Manifest V3. Popup POSTs `tab.url` to `/api/clip`. Options page stores server URL + API key in `chrome.storage.sync`. Guide in `chrome-extension/GUIDE.md`.

## Deployment

- **`scripts/deploy.sh`** — Rocky Linux 9.5. Auto-generates API key, installs Docker + compose plugin, Traefik + Let's Encrypt (TLS-ALPN), p12 export option.
- **`scripts/generate_icon.py`** — Renders the extension icon (256px supersampled → 128px).
- **`Dockerfile`** — uv-based build, Playwright + Chromium, non-root user.
- **`prompts/clip.md`** — Kimi system prompt for structured JSON extraction.

## Testing

All tests use `pytest-asyncio` (`asyncio_mode = "auto"`). HTTP mocking via `respx_mock` (pytest-respx fixture) and `monkeypatch` for env vars. Factory fixtures construct `Settings` directly with temp paths rather than reading `.env`.

Common test patterns:
- `respx_mock.get(...).respond(...)` for fetcher/web requests
- `respx_mock.post("https://api.kimi.com/coding/v1/chat/completions").respond(...)` for AI and worker tests
- `monkeypatch.setenv("VAULT_PATH", ...)` for worker tests
- `TestClient(app)` for API/web tests after monkeypatching `routes.settings` and `routes.store`

## Important conventions

- `Settings.api_keys` is comma-separated in env but a `list[str]` in code — the custom `CommaSeparatedEnvSource` handles the split.
- `JobStore` returns raw `dict` from SQLite rows, not model objects. Keys match the schema exactly.
- The `settings = Settings()` at module level in `worker.py`, `deps.py`, `routes.py`, etc. runs at import time. Test fixtures must `monkeypatch.setattr(routes, "settings", ...)` before first use.
- FastAPI `@router.on_event("startup")` is used for `store.init()` — may generate deprecation warnings on newer FastAPI versions but is consistent across the codebase.
- `playwright` is in main dependencies (not dev) because the Docker image requires it at runtime.
