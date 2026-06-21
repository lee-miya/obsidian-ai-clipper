# Task 13 Brief

Source plan: docs/superpowers/plans/2026-06-21-obsidian-ai-clipper-plan.md

## Task 13: Chrome Extension

**Files:**
- Create: `chrome-extension/manifest.json`
- Create: `chrome-extension/popup.html`
- Create: `chrome-extension/popup.js`
- Create: `chrome-extension/popup.css`
- Create: `chrome-extension/options.html`
- Create: `chrome-extension/options.js`
- Create: `chrome-extension/icons/icon-128.png` (placeholder)

**Interfaces:**
- Produces: Chrome extension that sends URL to `/api/clip`.

- [ ] **Step 1: Create `chrome-extension/manifest.json`**

```json
{
  "manifest_version": 3,
  "name": "Obsidian AI Clipper",
  "version": "1.0.0",
  "description": "Save web pages to Obsidian Vault via AI",
  "permissions": ["activeTab", "storage"],
  "optional_permissions": ["contextMenus"],
  "action": {
    "default_popup": "popup.html",
    "default_icon": {
      "128": "icons/icon-128.png"
    }
  },
  "icons": {
    "128": "icons/icon-128.png"
  },
  "options_page": "options.html"
}
```

- [ ] **Step 2: Create `chrome-extension/options.html`**

```html
<!doctype html>
<html>
<head><meta charset="utf-8"><title>Settings</title></head>
<body>
  <h1>Obsidian AI Clipper Settings</h1>
  <label>Server URL: <input type="url" id="serverUrl"></label><br><br>
  <label>API Key: <input type="password" id="apiKey"></label><br><br>
  <button id="save">Save</button>
  <script src="options.js"></script>
</body>
</html>
```

- [ ] **Step 3: Create `chrome-extension/options.js`**

```javascript
document.getElementById('save').addEventListener('click', async () => {
  const serverUrl = document.getElementById('serverUrl').value.replace(/\/$/, '');
  const apiKey = document.getElementById('apiKey').value;
  await chrome.storage.sync.set({ serverUrl, apiKey });
  alert('Saved');
});

(async () => {
  const { serverUrl, apiKey } = await chrome.storage.sync.get(['serverUrl', 'apiKey']);
  if (serverUrl) document.getElementById('serverUrl').value = serverUrl;
  if (apiKey) document.getElementById('apiKey').value = apiKey;
})();
```

- [ ] **Step 4: Create `chrome-extension/popup.html`**

```html
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <link rel="stylesheet" href="popup.css">
</head>
<body>
  <div id="status">Loading...</div>
  <button id="clip">Save to Vault</button>
  <script src="popup.js"></script>
</body>
</html>
```

- [ ] **Step 5: Create `chrome-extension/popup.js`**

```javascript
document.getElementById('clip').addEventListener('click', async () => {
  const status = document.getElementById('status');
  status.textContent = 'Saving...';

  const { serverUrl, apiKey } = await chrome.storage.sync.get(['serverUrl', 'apiKey']);
  if (!serverUrl || !apiKey) {
    status.textContent = 'Please configure server URL and API key first.';
    return;
  }

  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  try {
    const response = await fetch(`${serverUrl}/api/clip`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`,
        'X-Client-Version': '1.0.0',
      },
      body: JSON.stringify({ url: tab.url, submitted_at: new Date().toISOString(), client_version: '1.0.0' }),
    });
    const data = await response.json();
    if (response.ok) {
      status.textContent = `Saved. Job: ${data.job_id}`;
    } else {
      status.textContent = `Error: ${data.detail || response.statusText}`;
    }
  } catch (e) {
    status.textContent = `Network error: ${e.message}`;
  }
});

(async () => {
  document.getElementById('status').textContent = 'Ready';
})();
```

- [ ] **Step 6: Create `chrome-extension/popup.css`**

```css
body { width: 240px; padding: 1rem; font-family: system-ui, sans-serif; }
#status { margin-bottom: 0.75rem; font-size: 0.9rem; }
button { width: 100%; padding: 0.5rem; }
```

- [ ] **Step 7: Create placeholder icon**

Create a 128x128 PNG at `chrome-extension/icons/icon-128.png`. Use any simple image or placeholder.

- [ ] **Step 8: Commit**

```bash
git add chrome-extension/
git commit -m "feat: add Chrome extension"
```

---

