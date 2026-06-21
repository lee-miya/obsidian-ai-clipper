# Task 7 Brief

Source plan: docs/superpowers/plans/2026-06-21-obsidian-ai-clipper-plan.md

## Task 7: Kimi Code AI Client

**Files:**
- Create: `src/ai/kimi_client.py`
- Create: `prompts/clip.md`
- Test: `tests/test_ai_client.py`

**Interfaces:**
- Produces: `KimiClient` class with `async process(content: ExtractedContent) -> dict`.

- [ ] **Step 1: Write failing test**

```python
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
```

- [ ] **Step 2: Implement `src/ai/kimi_client.py`**

```python
import json
import httpx
from src.extractor.extractor import ExtractedContent

class KimiClient:
    def __init__(self, api_key: str, model: str = "kimi2.6"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.moonshot.cn/v1"

    async def process(self, content: ExtractedContent, url: str) -> dict:
        with open("prompts/clip.md", encoding="utf-8") as f:
            system_prompt = f.read()

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps({
                    "url": url,
                    "title": content.title,
                    "domain": url.split("/")[2],
                    "content": content.content,
                    "images": content.images,
                    "code_blocks": content.code_blocks,
                }, ensure_ascii=False)},
            ],
            "response_format": {"type": "json_object"},
        }

        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            raw = data["choices"][0]["message"]["content"]
            return json.loads(raw)
```

- [ ] **Step 3: Create `prompts/clip.md`**

```markdown
You are a helpful web content extractor. Given the metadata and extracted text of a web page, produce a JSON object with these fields:

- title: a clean, concise title
- category: one broad category for organizing in an Obsidian Vault (e.g., 人工智能, 编程开发, 产品设计, 未分类)
- tags: 3-7 relevant tags as a list of strings
- summary: 2-4 sentences summarizing the page
- content_markdown: the page content converted to clean Markdown, preserving code blocks and image references
- author: author name if known, otherwise empty string
- published_at: publication date in YYYY-MM-DD if known, otherwise empty string

Use Chinese for category, tags, summary, and title when the source is Chinese; otherwise use English.
Return only valid JSON.
```

- [ ] **Step 4: Run AI client tests**

Run: `pytest tests/test_ai_client.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/ai/kimi_client.py prompts/clip.md tests/test_ai_client.py
git commit -m "feat: add Kimi Code AI client"
```

---

