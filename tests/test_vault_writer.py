import pytest
import yaml
from pathlib import Path
from src.writer.vault_writer import save_clip
from src.extractor.extractor import ExtractedContent


async def test_save_clip_directory_structure(tmp_path):
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
    # Check directory structure: Clips/<category>/<date>-<slug>/index.md
    parts = path.parts
    assert "Clips" in parts
    assert "人工智能" in parts
    assert path.name == "index.md"
    text = path.read_text(encoding="utf-8")
    assert "Test" in text
    assert "source_url" in text


async def test_frontmatter_yaml_parses(tmp_path):
    extracted = ExtractedContent(title="T", content="Body", images=[], code_blocks=[])
    ai_result = {
        "title": "YAML Test",
        "category": "Test",
        "tags": ["tag1", "tag2"],
        "summary": "A summary",
        "content_markdown": "# Body",
        "author": "Author",
        "published_at": "2026-06-20",
    }
    path = await save_clip("job1", "https://example.com/y", ai_result, extracted, str(tmp_path))
    text = path.read_text(encoding="utf-8")
    # Extract frontmatter between --- markers
    assert text.startswith("---")
    end_marker = text.find("---", 3)
    assert end_marker != -1
    frontmatter_text = text[3:end_marker].strip()
    data = yaml.safe_load(frontmatter_text)
    assert data["title"] == "YAML Test"
    assert data["source_url"] == "https://example.com/y"
    assert data["domain"] == "example.com"
    assert data["category"] == "Test"
    assert data["tags"] == ["tag1", "tag2"]
    assert data["summary"] == "A summary"
    assert data["author"] == "Author"
    assert data["published_at"] == "2026-06-20"
    assert data["job_id"] == "job1"
    assert data["status"] == "done"


async def test_image_download_mocked(respx_mock, tmp_path):
    import httpx
    # Mock image download
    image_url = "https://example.com/image.png"
    respx_mock.get(image_url).mock(return_value=httpx.Response(200, content=b"fake_image_data", headers={"content-type": "image/png"}))

    extracted = ExtractedContent(
        title="T",
        content="Body",
        images=[{"src": image_url}],
        code_blocks=[],
    )
    ai_result = {
        "title": "Image Test",
        "category": "Test",
        "tags": [],
        "summary": "",
        "content_markdown": f"![img]({image_url})",
        "author": "",
        "published_at": "",
    }
    path = await save_clip("job2", "https://example.com/z", ai_result, extracted, str(tmp_path))
    text = path.read_text(encoding="utf-8")
    # Check that image was replaced with local filename
    assert "image_0.png" in text
    assert image_url not in text
    # Check image file exists
    image_file = path.parent / "image_0.png"
    assert image_file.exists()
    assert image_file.read_bytes() == b"fake_image_data"


async def test_collision_handling(tmp_path):
    extracted = ExtractedContent(title="T", content="Body", images=[], code_blocks=[])
    ai_result = {
        "title": "Same Title",
        "category": "Test",
        "tags": [],
        "summary": "",
        "content_markdown": "# Body",
        "author": "",
        "published_at": "",
    }
    # Save first clip
    path1 = await save_clip("job1", "https://example.com/a", ai_result, extracted, str(tmp_path))
    assert path1.exists()
    # Save second clip with same title
    path2 = await save_clip("job2", "https://example.com/b", ai_result, extracted, str(tmp_path))
    assert path2.exists()
    assert path1 != path2
    # Check directory names differ
    assert path1.parent.name != path2.parent.name
    assert path2.parent.name.endswith("-1")


async def test_fallback_empty_ai_result(tmp_path):
    extracted = ExtractedContent(title="Fallback Title", content="Fallback Body", images=[], code_blocks=[])
    ai_result = {}  # Empty AI result
    path = await save_clip("job3", "https://example.com/c", ai_result, extracted, str(tmp_path))
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "Fallback Title" in text
    assert "Fallback Body" in text
    # Check frontmatter has defaults
    assert text.startswith("---")
    end_marker = text.find("---", 3)
    frontmatter_text = text[3:end_marker].strip()
    data = yaml.safe_load(frontmatter_text)
    assert data["title"] == "Fallback Title"
    assert data["category"] == "未分类"
    assert data["tags"] == []
    assert data["summary"] == ""
    assert data["author"] == ""
    assert data["published_at"] == ""
    assert data["status"] == "done"
