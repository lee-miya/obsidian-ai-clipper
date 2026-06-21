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

**Key modules and their responsibilities:**

| Module | Responsibility |
|--------|---------------|
| `src/config.py` | Pydantic-settings with custom `CommaSeparatedEnvSource` for comma-delimited `API_KEYS`. Fields default to empty/false so tests can construct `Settings()` without a `.env` file. |
| `src/core/storage.py` | `JobStore` — async SQLite CRUD via `aiosqlite`. Each job has status, stage, retry_count, intermediates. No deletion — failed jobs persist forever. |
| `src/fetcher/fetcher.py` | `fetch_html()` — tries `StaticFetcher` (httpx, 180s timeout), falls back to `DynamicFetcher` (Playwright headless Chromium) on `httpx` errors only. |
| `src/extractor/extractor.py` | `extract()` — trafilatura for body text, BeautifulSoup for images/code blocks/title fallback. Returns `ExtractedContent` dataclass. |
| `src/ai/kimi_client.py` | `KimiClient.process()` — calls Kimi Code API (`api.kimi.com/coding/v1`). Model default: `kimi-for-coding`. Base URL configurable via `KIMI_BASE_URL`. No `response_format` param. Retries HTTP errors 3× with exponential backoff, extracts JSON from markdown fences if needed. Raises `KimiAPIError` on terminal failure. |
| `src/writer/vault_writer.py` | `save_clip()` — generates YAML frontmatter via `yaml.safe_dump`, downloads images, writes atomically (tmp file + rename), handles directory collisions. |
| `src/worker/worker.py` | `process_job()` — orchestrates the full pipeline. AI retry exhaustion → saves fallback content, marks `needs_review`. `CancelledError` re-raised at both retry and outer levels. Outer fatal errors → retry (status → pending) or final FAILED. **The module-level `settings = Settings()` reads env at import time; tests work around this with `monkeypatch.setenv`.** |
| `src/api/routes.py` | `POST /api/clip` (returns 202 + job_id, spawns background `asyncio.create_task`), `GET /api/jobs/{id}`. Both require `require_api_key` dep. |
| `src/api/deps.py` | `require_api_key` — verifies Bearer token, then applies rolling-window rate limits (IP: 10/60s, global: 100/60s). In-memory, resets on restart. |
| `src/main.py` | FastAPI app factory — mounts both API and Web routers, adds security headers middleware (X-Content-Type-Options, X-Frame-Options, CSP). |
| `src/web/routes.py` | Jinja2 HTML pages: `/web` (list), `/web/clips/{id}` (detail), `/web/failed`, `/web/queue`. |
| `src/utils/url.py` | `validate_public_url()` — rejects non-http/https, localhost, private IPs (IPv4+IPv6). |
| `src/core/security.py` | `verify_api_key()` — checks `Bearer <key>` against allowed list. |

**Chrome extension** (`chrome-extension/`): Manifest V3, popup that POSTs `tab.url` to `/api/clip`, options page for server URL + API key stored in `chrome.storage.sync`. See `chrome-extension/GUIDE.md` for installation and usage.

**Deployment** (`scripts/deploy.sh`): Interactive bash script for Rocky Linux 9.5. Auto-generates API key, installs Docker, configures Traefik + Let's Encrypt TLS, offers optional p12 export. See `README.md` for quick start.

**Prompt template:** `prompts/clip.md` — the system prompt Kimi receives. Instructs structured JSON output with title, category, tags, summary, content_markdown, author, published_at.

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
