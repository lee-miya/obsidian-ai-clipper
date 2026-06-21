# Task 6 Brief

Source plan: docs/superpowers/plans/2026-06-21-obsidian-ai-clipper-plan.md

## Task 6: Content Extractor

**Files:**
- Create: `src/extractor/extractor.py`
- Test: `tests/test_extractor.py`

**Interfaces:**
- Produces: `ExtractedContent(title, content, images, code_blocks, author, published_at)` dataclass and `extract(html: str, url: str) -> ExtractedContent` function.

- [ ] **Step 1: Write failing test**

```python
from src.extractor.extractor import extract

HTML = """
<html><head><title>Test Article</title></head>
<body>
<article>
<h1>Test Article</h1>
<p>This is the main content.</p>
<img src="https://example.com/img.png" alt="diagram">
<pre><code class="python">print("hi")</code></pre>
</article>
</body></html>
"""

def test_extract_content():
    result = extract(HTML, "https://example.com")
    assert result.title == "Test Article"
    assert "main content" in result.content
    assert len(result.images) == 1
    assert len(result.code_blocks) == 1
```

- [ ] **Step 2: Implement `src/extractor/extractor.py`**

```python
from dataclasses import dataclass, field
from bs4 import BeautifulSoup
import trafilatura

@dataclass
class ExtractedContent:
    title: str = ""
    content: str = ""
    images: list[dict] = field(default_factory=list)
    code_blocks: list[dict] = field(default_factory=list)
    author: str = ""
    published_at: str = ""

def extract(html: str, url: str) -> ExtractedContent:
    extracted = ExtractedContent()

    title = trafilatura.extract(html, output_format="json", include_comments=False, include_tables=True)
    if title:
        import json
        data = json.loads(title)
        extracted.title = data.get("title", "")
        extracted.content = data.get("raw_text", "")

    soup = BeautifulSoup(html, "html.parser")

    if not extracted.title:
        title_tag = soup.find("title")
        extracted.title = title_tag.get_text(strip=True) if title_tag else ""

    for img in soup.find_all("img"):
        src = img.get("src")
        if src:
            from urllib.parse import urljoin
            extracted.images.append({
                "src": urljoin(url, src),
                "alt": img.get("alt", ""),
            })

    for pre in soup.find_all("pre"):
        code = pre.find("code")
        lang = ""
        if code:
            classes = code.get("class", [])
            for c in classes:
                if c.startswith("language-"):
                    lang = c.replace("language-", "")
                    break
        extracted.code_blocks.append({
            "language": lang,
            "code": pre.get_text(),
        })

    return extracted
```

- [ ] **Step 3: Run extractor tests**

Run: `pytest tests/test_extractor.py -v`  
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add src/extractor/extractor.py tests/test_extractor.py
git commit -m "feat: add content extractor"
```

---

