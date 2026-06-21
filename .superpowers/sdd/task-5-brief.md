# Task 5 Brief

Source plan: docs/superpowers/plans/2026-06-21-obsidian-ai-clipper-plan.md

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

