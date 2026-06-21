import pytest
from src.fetcher.static_fetcher import StaticFetcher

async def test_fetch_html_success(respx_mock):
    respx_mock.get("https://example.com").respond(200, text="<html><body>Hello</body></html>")
    fetcher = StaticFetcher()
    html = await fetcher.fetch("https://example.com")
    assert "Hello" in html
