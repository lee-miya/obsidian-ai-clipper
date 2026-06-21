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
