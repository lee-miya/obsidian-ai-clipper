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
