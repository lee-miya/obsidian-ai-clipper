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
