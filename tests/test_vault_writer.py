import pytest
from pathlib import Path
from src.writer.vault_writer import save_clip
from src.extractor.extractor import ExtractedContent

async def test_save_clip(tmp_path):
    extracted = ExtractedContent(title="T", content="Body", images=[], code_blocks=[])
    ai_result = {
        "title": "Test",
        "category": "人工智能",
        "tags": ["AI"],
        "summary": "Summary",
        "content_markdown": "# Test\n\nBody",
        "author": "A",
        "published_at": "2026-06-20",
    }
    path = await save_clip("clip_abc", "https://example.com/x", ai_result, extracted, str(tmp_path))
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "Test" in text
    assert "source_url" in text
