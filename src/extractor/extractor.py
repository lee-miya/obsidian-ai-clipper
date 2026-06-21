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
        extracted.content = data.get("raw_text", data.get("text", ""))

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
