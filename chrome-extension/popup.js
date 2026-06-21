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
