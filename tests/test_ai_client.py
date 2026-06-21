import httpx
import pytest
from src.ai.kimi_client import KimiClient, KimiAPIError
from src.extractor.extractor import ExtractedContent

async def test_process_calls_api(respx_mock):
    client = KimiClient(api_key="test")
    respx_mock.post("https://api.kimi.com/coding/v1/chat/completions").respond(json={
        "choices": [{"message": {"content": '{"title":"T","category":"未分类","tags":[],"summary":"S","content_markdown":"MD","author":"","published_at":""}'}}]
    })
    content = ExtractedContent(title="Original", content="Body text", images=[], code_blocks=[])
    result = await client.process(content, url="https://example.com")
    assert result["title"] == "T"

async def test_process_retries_on_http_error(respx_mock):
    client = KimiClient(api_key="test", model="kimi-k2.6")
    route = respx_mock.post("https://api.kimi.com/coding/v1/chat/completions")
    route.side_effect = [
        httpx.Response(500),
        httpx.Response(500),
        httpx.Response(200, json={
            "choices": [{"message": {"content": '{"title":"R","category":"未分类","tags":[],"summary":"S","content_markdown":"MD","author":"","published_at":""}'}}]
        }),
    ]
    content = ExtractedContent(title="Original", content="Body text", images=[], code_blocks=[])
    result = await client.process(content, url="https://example.com")
    assert result["title"] == "R"

async def test_process_raises_on_persistent_http_error(respx_mock):
    client = KimiClient(api_key="test", model="kimi-k2.6")
    respx_mock.post("https://api.kimi.com/coding/v1/chat/completions").respond(500)
    content = ExtractedContent(title="Original", content="Body text", images=[], code_blocks=[])
    with pytest.raises(KimiAPIError):
        await client.process(content, url="https://example.com")

async def test_process_extracts_json_from_markdown_fences(respx_mock):
    client = KimiClient(api_key="test")
    respx_mock.post("https://api.kimi.com/coding/v1/chat/completions").respond(json={
        "choices": [{"message": {"content": '```json\n{"title":"Fenced","category":"未分类","tags":[],"summary":"S","content_markdown":"MD","author":"","published_at":""}\n```'}}]
    })
    content = ExtractedContent(title="Original", content="Body text", images=[], code_blocks=[])
    result = await client.process(content, url="https://example.com")
    assert result["title"] == "Fenced"

async def test_process_raises_on_malformed_json(respx_mock):
    client = KimiClient(api_key="test")
    respx_mock.post("https://api.kimi.com/coding/v1/chat/completions").respond(json={
        "choices": [{"message": {"content": 'not-json-at-all'}}]
    })
    content = ExtractedContent(title="Original", content="Body text", images=[], code_blocks=[])
    with pytest.raises(KimiAPIError):
        await client.process(content, url="https://example.com")
