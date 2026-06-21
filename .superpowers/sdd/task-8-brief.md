# Task 8 Brief

Source plan: docs/superpowers/plans/2026-06-21-obsidian-ai-clipper-plan.md

## Task 8: Vault Writer

**Files:**
- Create: `src/writer/vault_writer.py`
- Test: `tests/test_vault_writer.py`

**Interfaces:**
- Produces: `async save_clip(job_id, url, ai_result, extracted, vault_root) -> Path`.

- [ ] **Step 1: Write failing test**

```python
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
```

- [ ] **Step 2: Implement `src/writer/vault_writer.py`**

```python
import re
import httpx
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from src.extractor.extractor import ExtractedContent

SLUG_MAX = 60

def safe_filename(name: str) -> str:
    name = re.sub(r"[^\w一-龥-]+", "-", name).strip("-")
    return name[:SLUG_MAX]

async def download_image(url: str, dest: Path) -> str:
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        ext = response.headers.get("content-type", "").split("/")[-1]
        if not ext or ext not in {"png", "jpg", "jpeg", "gif", "webp", "svg"}:
            ext = "png"
        filename = f"image_{dest.parent.name}_{dest.name}.{ext}"
        image_path = dest.parent / filename
        image_path.write_bytes(response.content)
        return filename

async def save_clip(
    job_id: str,
    url: str,
    ai_result: dict,
    extracted: ExtractedContent,
    vault_root: str,
) -> Path:
    category = safe_filename(ai_result.get("category") or "未分类")
    title = ai_result.get("title") or extracted.title or "untitled"
    date_prefix = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    slug = safe_filename(title) or "clip"
    dir_name = f"{date_prefix}-{slug}"
    clip_dir = Path(vault_root) / "Clips" / category / dir_name
    clip_dir.mkdir(parents=True, exist_ok=True)

    index_path = clip_dir / "index.md"
    counter = 1
    while index_path.exists():
        clip_dir = Path(vault_root) / "Clips" / category / f"{dir_name}-{counter}"
        clip_dir.mkdir(parents=True, exist_ok=True)
        index_path = clip_dir / "index.md"
        counter += 1

    md_content = ai_result.get("content_markdown") or extracted.content
    image_map = {}
    for idx, img in enumerate(extracted.images):
        try:
            filename = await download_image(img["src"], clip_dir / f"img_{idx}")
            image_map[img["src"]] = filename
        except Exception:
            image_map[img["src"]] = img["src"]

    for original, replacement in image_map.items():
        md_content = md_content.replace(original, replacement)

    frontmatter = f"""---
title: "{title}"
source_url: "{url}"
domain: "{urlparse(url).netloc}"
category: "{category}"
tags:
{chr(10).join(f'  - "{t}"' for t in ai_result.get('tags', []))}
summary: "{ai_result.get('summary', '')}"
author: "{ai_result.get('author', '')}"
published_at: "{ai_result.get('published_at', '')}"
clipped_at: "{datetime.now(timezone.utc).isoformat()}"
job_id: "{job_id}"
status: "done"
---

{md_content}
"""

    temp_path = clip_dir / ".index.md.tmp"
    temp_path.write_text(frontmatter, encoding="utf-8")
    temp_path.replace(index_path)
    return index_path
```

- [ ] **Step 3: Run vault writer tests**

Run: `pytest tests/test_vault_writer.py -v`  
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add src/writer/vault_writer.py tests/test_vault_writer.py
git commit -m "feat: add vault writer with image download"
```

---

