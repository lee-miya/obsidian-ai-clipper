import pytest
from src.ai.kimi_client import KimiClient
from src.extractor.extractor import ExtractedContent

async def test_process_calls_api(respx_mock):
    client = KimiClient(api_key="test", model="kimi2.6")
    respx_mock.post("https://api.moonshot.cn/v1/chat/completions").respond(json={
        "choices": [{"message": {"content": '{"title":"T","category":"未分类","tags":[],"summary":"S","content_markdown":"MD","author":"","published_at":""}'}}]
    })
    content = ExtractedContent(title="Original", content="Body text", images=[], code_blocks=[])
    result = await client.process(content, url="https://example.com")
    assert result["title"] == "T"
