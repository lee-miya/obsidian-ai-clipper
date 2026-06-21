Task 5 fix instructions:

1. Remove the committed `src/fetcher/__pycache__` directory from git and create a `.gitignore` file with standard Python ignores:
   - `__pycache__/`
   - `*.pyc`
   - `*.pyo`
   - `*.egg-info/`
   - `.venv/`
   - `.env`
   - `*.db`
   - `.pytest_cache/`
   - `.mypy_cache/`
   - `.ruff_cache/`
   - `data/`
   - `letsencrypt/`

2. Narrow the exception handling in `src/fetcher/fetcher.py` to catch only httpx errors:
```python
import httpx
from src.fetcher.static_fetcher import StaticFetcher
from src.fetcher.dynamic_fetcher import DynamicFetcher

async def fetch_html(url: str) -> str:
    static = StaticFetcher()
    try:
        return await static.fetch(url)
    except (httpx.HTTPStatusError, httpx.RequestError, httpx.TimeoutException):
        dynamic = DynamicFetcher()
        return await dynamic.fetch(url)
```

3. Use context managers in `src/fetcher/dynamic_fetcher.py`:
```python
from playwright.async_api import async_playwright

class DynamicFetcher:
    async def fetch(self, url: str) -> str:
        async with async_playwright() as p:
            async with await p.chromium.launch(headless=True) as browser:
                async with browser.new_context() as context:
                    page = await context.new_page()
                    await page.goto(url, timeout=180000, wait_until="networkidle")
                    return await page.content()
```

4. Add tests in `tests/test_fetcher.py`:
   - Test static fetcher failure falls back to dynamic fetcher (mock the dynamic path)
   - Test dynamic fetcher returns HTML
   - Note: Playwright dynamic tests may be slow/skip in CI; use mocks where possible.

5. Run all tests with `uv run pytest tests/test_fetcher.py -v` and ensure they pass.

6. Commit with message: `fix: address Task 5 review feedback (pycache, exception handling, resource cleanup)`

Write a report to `.superpowers/sdd/task-5-report.md` appending the fix details.
