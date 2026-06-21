from playwright.async_api import async_playwright

class DynamicFetcher:
    async def fetch(self, url: str) -> str:
        async with async_playwright() as p:
            async with await p.chromium.launch(headless=True) as browser:
                async with browser.new_context() as context:
                    page = await context.new_page()
                    await page.goto(url, timeout=180000, wait_until="networkidle")
                    return await page.content()
