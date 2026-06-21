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
