import httpx

class StaticFetcher:
    async def fetch(self, url: str) -> str:
        async with httpx.AsyncClient(timeout=180.0, follow_redirects=True) as client:
            response = await client.get(url, headers={"User-Agent": "ObsidianAIClipper/1.0"})
            response.raise_for_status()
            return response.text
