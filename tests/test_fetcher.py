import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from src.fetcher.static_fetcher import StaticFetcher
from src.fetcher.dynamic_fetcher import DynamicFetcher
from src.fetcher.fetcher import fetch_html

async def test_fetch_html_success(respx_mock):
    respx_mock.get("https://example.com").respond(200, text="<html><body>Hello</body></html>")
    fetcher = StaticFetcher()
    html = await fetcher.fetch("https://example.com")
    assert "Hello" in html

async def test_fetch_html_fallback_to_dynamic(respx_mock):
    """Test that static fetcher failure falls back to dynamic fetcher."""
    respx_mock.get("https://example.com").mock(side_effect=httpx.HTTPStatusError(
        "Server error", request=None, response=AsyncMock(status_code=500)
    ))

    with patch("src.fetcher.fetcher.DynamicFetcher") as mock_dynamic:
        mock_instance = AsyncMock()
        mock_instance.fetch = AsyncMock(return_value="<html><body>Dynamic</body></html>")
        mock_dynamic.return_value = mock_instance

        html = await fetch_html("https://example.com")
        assert "Dynamic" in html
        mock_instance.fetch.assert_called_once_with("https://example.com")

async def test_dynamic_fetcher_returns_html():
    """Test dynamic fetcher returns HTML."""
    with patch("src.fetcher.dynamic_fetcher.async_playwright") as mock_playwright:
        mock_page = AsyncMock()
        mock_page.content = AsyncMock(return_value="<html><body>Test</body></html>")

        mock_context = MagicMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.__aenter__ = AsyncMock(return_value=mock_context)
        mock_context.__aexit__ = AsyncMock(return_value=False)

        # Make new_context return an async context manager
        class AsyncContextManager:
            async def __aenter__(self):
                return mock_context
            async def __aexit__(self, *args):
                return False

        mock_browser = MagicMock()
        mock_browser.new_context = lambda: AsyncContextManager()
        mock_browser.__aenter__ = AsyncMock(return_value=mock_browser)
        mock_browser.__aexit__ = AsyncMock(return_value=False)

        mock_playwright_obj = MagicMock()
        mock_playwright_obj.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_playwright_obj.__aenter__ = AsyncMock(return_value=mock_playwright_obj)
        mock_playwright_obj.__aexit__ = AsyncMock(return_value=False)

        mock_playwright.return_value = mock_playwright_obj

        fetcher = DynamicFetcher()
        html = await fetcher.fetch("https://example.com")
        assert "Test" in html
