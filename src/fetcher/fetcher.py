from src.fetcher.static_fetcher import StaticFetcher
from src.fetcher.dynamic_fetcher import DynamicFetcher

async def fetch_html(url: str) -> str:
    static = StaticFetcher()
    try:
        return await static.fetch(url)
    except Exception:
        dynamic = DynamicFetcher()
        return await dynamic.fetch(url)
