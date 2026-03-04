/**
 * MCP Hub — Setup Panel JS
 * NerdOptimize
 */

const API = 'http://localhost:8000';

// ─── Utils ────────────────────────────────────────────────────────────────────

function toast(msg, type = 'info', duration = 3500) {
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.textContent = msg;
  document.getElementById('toast-container').appendChild(el);
  setTimeout(() => el.remove(), duration);
}

async function apiFetch(path, opts = {}) {
  const res = await fetch(`${API}${path}`, {
    headers: { 'Content-Type': 'application/json', ...opts.headers },
    ...opts,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || JSON.stringify(err));
  }
  return res.json();
}

function setLoading(btn, loading, label = null) {
  if (loading) {
    btn.disabled = true;
    btn.dataset.originalHtml = btn.innerHTML;
    btn.innerHTML = `<span class="spinner"></span>${label ? ' ' + label : ''}`;
  } else {
    btn.disabled = false;
    if (btn.dataset.originalHtml) btn.innerHTML = btn.dataset.originalHtml;
  }
}

function truncateFilename(name) {
  if (!name || name.length <= 30) return name;
  const last9 = name.slice(-9);
  const prefix = name.slice(0, name.length - 9);
  const showStart = Math.min(prefix.length, 20);
  return prefix.slice(0, showStart) + 'xxxxxxxxx' + last9;
}

function formatDisplayFilename(name) {
  if (!name) return null;
  const truncated = truncateFilename(name);
  return truncated === name ? `✅ ${name}` : `✅ ${truncated}`;
}

// ─── Status Rendering ─────────────────────────────────────────────────────────

const STATUS_LABELS = {
  connected: 'เชื่อมต่อแล้ว',
  failed:    'เชื่อมไม่สำเร็จ',
  disconnected: 'ยังไม่เชื่อมต่อ',
  offline:   'ออฟไลน์',
  online:    'ออนไลน์',
};

function updateBadge(id, status) {
  const badge = document.getElementById(`badge-${id}`);
  if (!badge) return;
  const dot  = badge.querySelector('.dot');
  const text = badge.querySelector('.badge-text');

  dot.className = 'dot';
  text.className = 'badge-text';

  if (status === 'connected') {
    dot.classList.add('dot-green');
    text.classList.add('connected');
    text.textContent = 'เชื่อมต่อแล้ว';
  } else if (status === 'failed') {
    dot.classList.add('dot-orange');
    text.classList.add('failed');
    text.textContent = 'เชื่อมไม่สำเร็จ';
  } else {
    dot.classList.add('dot-red');
    text.textContent = 'ยังไม่เชื่อมต่อ';
  }
}

function updateCard(id, status) {
  const card = document.getElementById(`section-${id}`);
  if (!card) return;
  card.classList.remove('connected', 'failed');
  if (status === 'connected') card.classList.add('connected');
  else if (status === 'failed') card.classList.add('failed');
}

function updateStatusRow(id, status, msg = null) {
  const row = document.getElementById(`srow-${id}`);
  if (!row) return;
  const dot  = row.querySelector('.dot');
  const text = row.querySelector('.srow-msg');

  dot.className = 'dot';
  text.className = 'srow-msg';

  if (status === 'connected' || status === 'online') {
    dot.classList.add('dot-green');
    text.classList.add('connected');
    text.textContent = msg || STATUS_LABELS[status] || status;
  } else if (status === 'failed') {
    dot.classList.add('dot-orange');
    text.classList.add('failed');
    text.textContent = msg || 'เชื่อมไม่สำเร็จ';
  } else {
    dot.classList.add('dot-red');
    text.classList.add('offline');
    text.textContent = msg || STATUS_LABELS[status] || status;
  }
}

function updateChip(id, status) {
  const chip = document.getElementById(`chip-${id}`);
  if (!chip) return;
  chip.className = 'svc-chip';
  if (status === 'connected' || status === 'online') {
    chip.classList.add('ok');
    chip.textContent = `${id.toUpperCase()} ✅`;
  } else if (status === 'failed') {
    chip.classList.add('warn');
    chip.textContent = `${id.toUpperCase()} ⚠️`;
  } else {
    chip.classList.add('err');
    chip.textContent = `${id.toUpperCase()} ❌`;
  }
}

function updateOnlineBar(isOnline) {
  const bar  = document.getElementById('online-bar');
  const pill = document.getElementById('online-pill');
  if (isOnline) {
    bar.classList.add('online');
    pill.classList.add('online');
    pill.textContent = '● ONLINE';
  } else {
    bar.classList.remove('online');
    pill.classList.remove('online');
    pill.textContent = '● OFFLINE';
  }
}

function updateConnectAllButton(isOnline) {
  const btn = document.getElementById('btn-connect-all');
  if (!btn) return;
  const CONNECT_ALL_ICON = '<svg width="15" height="15" viewBox="0 0 15 15" fill="none"><path d="M7.5 1v13M1 7.5h13" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>';
  if (isOnline) {
    btn.disabled = true;
    btn.title = 'MCP Hub is already running. Use Stop Connector to pause.';
    btn.innerHTML = `${CHECK_ICON} MCP Hub Online`;
    btn.classList.add('btn-connect-online');
  } else {
    btn.disabled = false;
    btn.title = '';
    btn.innerHTML = `${CONNECT_ALL_ICON} Connect &amp; Start MCP Hub`;
    btn.classList.remove('btn-connect-online');
  }
}

function updateStopConnectorButton(isOnline) {
  const btn = document.getElementById('btn-stop-connector');
  if (!btn) return;
  btn.disabled = !isOnline;
  if (isOnline) {
    btn.classList.remove('btn-stop-disabled');
  } else {
    btn.classList.add('btn-stop-disabled');
  }
}

// ─── Refresh Status ───────────────────────────────────────────────────────────

async function refreshStatus() {
  try {
    const data = await apiFetch('/api/status');

    // GSC
    const gscStatus = data.gsc.status;
    updateBadge('gsc', gscStatus);
    updateCard('gsc', gscStatus);
    updateStatusRow('gsc', gscStatus);
    updateChip('gsc', gscStatus);
    updateUploadFilename('gsc', data.gsc.uploaded_filename);
    updateConnectButton('gsc', gscStatus);

    // GA4
    const ga4Status = data.ga4.status;
    updateBadge('ga4', ga4Status);
    updateCard('ga4', ga4Status);
    updateStatusRow('ga4', ga4Status);
    updateChip('ga4', ga4Status);
    updateUploadFilename('ga4', data.ga4.uploaded_filename);
    updateConnectButton('ga4', ga4Status);

    // Ahrefs
    const ahrefsStatus = data.ahrefs.status;
    updateBadge('ahrefs', ahrefsStatus);
    updateCard('ahrefs', ahrefsStatus);
    updateStatusRow('ahrefs', ahrefsStatus);
    updateChip('ahrefs', ahrefsStatus);
    if (data.ahrefs.has_credentials) loadAhrefsPreview(false);

    // ngrok
    const ngrokStatus = data.ngrok.status;
    const tunnelActive = data.ngrok.tunnel_active;
    const effectiveNgrokStatus = tunnelActive ? 'connected' : ngrokStatus;
    updateBadge('ngrok', effectiveNgrokStatus);
    updateCard('ngrok', effectiveNgrokStatus);
    updateStatusRow('ngrok', effectiveNgrokStatus);
    updateChip('ngrok', effectiveNgrokStatus);

    if (data.ngrok.mcp_url) {
      showMcpUrl(data.ngrok.mcp_url);
      if (data.ngrok.static_domain) {
        document.getElementById('ngrok-domain').value = data.ngrok.static_domain;
      }
    }
    if (data.ngrok.has_credentials) loadNgrokPreview(false);

    // Connector log
    refreshConnectorLog();

    // Hub
    const hubOnline = data.mcp_hub.online;
    updateStatusRow('hub', hubOnline ? 'online' : 'offline', hubOnline ? 'ออนไลน์' : 'ออฟไลน์');
    updateOnlineBar(hubOnline);
    updateConnectAllButton(hubOnline);
    updateStopConnectorButton(hubOnline);

  } catch (e) {
    console.warn('Status refresh failed:', e.message);
  }
}

function showMcpUrl(url) {
  const box  = document.getElementById('mcp-url-box');
  const text = document.getElementById('mcp-url-text');
  box.style.display = 'block';
  text.textContent  = url;
}

function updateUploadFilename(service, filename) {
  const nameEl = document.getElementById(`${service}-file-name`);
  const label = document.getElementById(`${service}-upload-label`);
  if (!nameEl) return;
  if (filename) {
    nameEl.textContent = formatDisplayFilename(filename);
    label && label.classList.add('has-file');
  } else {
    nameEl.textContent = 'Upload client_secret.json';
    label && label.classList.remove('has-file');
  }
}

const OAUTH_BTN_LABELS = { gsc: 'GSC', ga4: 'GA4' };
const CHECK_ICON = '<svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M2 7l3 3 7-7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
const CONNECT_ICON = '<svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M7 1a6 6 0 1 0 0 12A6 6 0 0 0 7 1Z" stroke="currentColor" stroke-width="1.2" fill="none"/><path d="M7 4v3l2 2" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg>';

function updateConnectButton(service, status) {
  const btn = document.getElementById(`${service}-oauth-btn`);
  if (!btn) return;
  const connected = status === 'connected';
  const label = OAUTH_BTN_LABELS[service] || service.toUpperCase();
  btn.disabled = connected;
  btn.title = connected ? 'เชื่อมต่อแล้ว' : '';
  if (connected) {
    btn.innerHTML = `${CHECK_ICON} [Connected] Google Account — ${label}`;
  } else {
    btn.innerHTML = `${CONNECT_ICON} Connect Google Account — ${label}`;
  }
}

async function refreshConnectorLog() {
  try {
    const data = await apiFetch('/api/connector-log');
    const list = document.getElementById('connector-log-list');
    const empty = document.getElementById('connector-log-empty');
    const countEl = document.getElementById('connector-log-count');
    if (!list || !countEl) return;

    const total = data.total_connections || 0;
    countEl.textContent = `${total} เครื่องที่ต่อเข้ามา`;

    const entries = data.entries || [];
    if (entries.length === 0) {
      empty.style.display = 'block';
      empty.textContent = 'ยังไม่มี connection';
      list.querySelectorAll('.connector-log-entry').forEach(el => el.remove());
    } else {
      empty.style.display = 'none';
      list.querySelectorAll('.connector-log-entry').forEach(el => el.remove());
      entries.forEach((e) => {
        const time = e.connected_at_iso || e.last_activity_iso || '—';
        const client = e.client_type || 'Unknown';
        const status = 'เชื่อมต่อแล้ว';
        const statusCls = 'conn-connected';
        const div = document.createElement('div');
        div.className = 'connector-log-entry';
        div.innerHTML = `<span class="conn-time">${time}</span><span class="conn-client">${client}</span><span class="conn-status ${statusCls}">${status}</span>`;
        list.appendChild(div);
      });
    }
  } catch (_) {
    const countEl = document.getElementById('connector-log-count');
    if (countEl) countEl.textContent = '0 เครื่องที่ต่อเข้ามา';
  }
}

// ─── File Upload ──────────────────────────────────────────────────────────────

function setupFileUpload(service) {
  const input  = document.getElementById(`${service}-file`);
  const label  = document.getElementById(`${service}-upload-label`);
  const nameEl = document.getElementById(`${service}-file-name`);
  const delBtn = document.getElementById(`${service}-delete-secret`);

  if (!input) return;

  input.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(`${API}/api/upload-secret/${service}`, {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) throw new Error('Upload failed');
      const data = await res.json();
      const fn = data.filename || file.name;
      label.classList.add('has-file');
      nameEl.textContent = formatDisplayFilename(fn);
      toast(`${service.toUpperCase()} client_secret.json uploaded`, 'success');
    } catch (err) {
      toast(`Upload failed: ${err.message}`, 'error');
    }
    input.value = '';
  });

  delBtn.addEventListener('click', async () => {
    try {
      await fetch(`${API}/api/upload-secret/${service}`, { method: 'DELETE' });
    } catch (_) { /* ignore */ }
    label.classList.remove('has-file');
    nameEl.textContent = 'Upload client_secret.json';
    toast(`${service.toUpperCase()} secret file cleared`, 'info');
  });
}

// ─── OAuth Flow ───────────────────────────────────────────────────────────────

function startOAuthPolling(service, btn, popup) {
  let attempts = 0;
  const MAX = 120; // 2 minutes
  let cleared = false;

  function stopLoadingAndUpdate() {
    if (cleared) return;
    cleared = true;
    clearInterval(interval);
    if (popup) clearInterval(closeCheck);
    setLoading(btn, false);
  }

  async function checkStatusAndUpdate() {
    try {
      const result = await apiFetch(`/api/oauth/poll/${service}`);
      if (result.status === 'connected') {
        stopLoadingAndUpdate();
        updateBadge(service, 'connected');
        updateCard(service, 'connected');
        updateStatusRow(service, 'connected');
        updateChip(service, 'connected');
        updateConnectButton(service, 'connected');
        toast(`${service.toUpperCase()} connected successfully!`, 'success');
      } else if (result.status === 'error') {
        stopLoadingAndUpdate();
        updateConnectButton(service, 'disconnected');
        toast(`OAuth failed: ${result.error}`, 'error');
      }
    } catch (_) {}
  }

  const interval = setInterval(() => {
    attempts++;
    if (attempts >= MAX) {
      stopLoadingAndUpdate();
      updateConnectButton(service, 'disconnected');
      toast('OAuth timed out. Please try again.', 'error');
      return;
    }
    checkStatusAndUpdate();
  }, 1000);

  // เมื่อปิด popup ให้เช็ค status อีกครั้ง แล้วอัปเดตปุ่ม (ถ้าเชื่อมต่อแล้วจะแสดง [Connected])
  let closeCheck;
  if (popup) {
    closeCheck = setInterval(() => {
      if (popup.closed) {
        stopLoadingAndUpdate();
        checkStatusAndUpdate();
      }
    }, 500);
  }
}

function setupOAuthButton(service) {
  const btn = document.getElementById(`${service}-oauth-btn`);
  if (!btn) return;

  btn.addEventListener('click', async () => {
    setLoading(btn, true, 'Opening Google login...');
    try {
      const data = await apiFetch(`/api/oauth/start/${service}`);
      const popup = window.open(data.auth_url, `oauth-${service}`, 'width=600,height=700,scrollbars=yes');
      if (!popup) {
        toast('Popup blocked! Allow popups for this page and try again.', 'error');
        setLoading(btn, false);
        return;
      }
      setLoading(btn, true, 'Waiting for Google...');
      startOAuthPolling(service, btn, popup);
    } catch (err) {
      setLoading(btn, false);
      toast(`Error: ${err.message}`, 'error');
    }
  });
}

// ─── Disconnect ───────────────────────────────────────────────────────────────

function setupDisconnect(service) {
  const btn = document.getElementById(`${service}-disconnect`);
  if (!btn) return;

  btn.addEventListener('click', async () => {
    try {
      await apiFetch(`/api/credentials/${service}`, { method: 'DELETE' });
      updateBadge(service, 'disconnected');
      updateCard(service, 'disconnected');
      updateStatusRow(service, 'disconnected');
      updateChip(service, 'disconnected');
      updateUploadFilename(service, null);
      updateConnectButton(service, 'disconnected');
      toast(`${service.toUpperCase()} disconnected`, 'info');

      if (service === 'ahrefs') {
        const k = document.getElementById('ahrefs-key');
        if (k) k.value = '';
      }
      if (service === 'ngrok') {
        const t = document.getElementById('ngrok-token');
        if (t) t.value = '';
        document.getElementById('mcp-url-box').style.display = 'none';
      }
    } catch (err) {
      toast(`Error: ${err.message}`, 'error');
    }
  });
}

// ─── Ahrefs API Key ───────────────────────────────────────────────────────────

async function loadAhrefsPreview(reveal) {
  try {
    const data = await apiFetch(`/api/credentials/ahrefs/preview?reveal=${reveal}`);
    const keyInput = document.getElementById('ahrefs-key');
    if (keyInput && data.has_credentials && data.value) {
      keyInput.value = data.value;
    }
  } catch (_) {}
}

function setupAhrefs() {
  const saveBtn   = document.getElementById('ahrefs-save-btn');
  const toggleBtn = document.getElementById('ahrefs-toggle-key');
  const keyInput  = document.getElementById('ahrefs-key');

  saveBtn.addEventListener('click', async () => {
    const key = keyInput.value.trim();
    if (!key) {
      toast('Please enter an Ahrefs API key', 'error');
      return;
    }
    setLoading(saveBtn, true, 'Saving...');
    try {
      await apiFetch('/api/ahrefs/save-key', {
        method: 'POST',
        body: JSON.stringify({ api_key: key }),
      });
      toast('Ahrefs API key saved', 'success');
      updateBadge('ahrefs', 'connected');
      updateCard('ahrefs', 'connected');
      updateStatusRow('ahrefs', 'connected');
      updateChip('ahrefs', 'connected');
      loadAhrefsPreview(false);
    } catch (err) {
      toast(`Error: ${err.message}`, 'error');
    } finally {
      setLoading(saveBtn, false);
    }
  });

  let showing = false;
  toggleBtn.addEventListener('click', async () => {
    showing = !showing;
    if (showing) {
      await loadAhrefsPreview(true);
      toggleBtn.title = 'ซ่อน';
    } else {
      await loadAhrefsPreview(false);
      toggleBtn.title = 'เปิดดู';
    }
  });
}

// ─── ngrok ────────────────────────────────────────────────────────────────────

async function loadNgrokPreview(reveal) {
  try {
    const data = await apiFetch(`/api/credentials/ngrok/preview?reveal=${reveal}`);
    const tokenInput = document.getElementById('ngrok-token');
    if (tokenInput && data.has_credentials && data.value) {
      tokenInput.value = data.value;
    }
  } catch (_) {}
}

function setupNgrok() {
  const tokenInput  = document.getElementById('ngrok-token');
  const toggleToken = document.getElementById('ngrok-toggle-token');

  let showingToken = false;
  toggleToken.addEventListener('click', async () => {
    showingToken = !showingToken;
    if (showingToken) {
      await loadNgrokPreview(true);
      toggleToken.title = 'ซ่อน';
    } else {
      await loadNgrokPreview(false);
      toggleToken.title = 'เปิดดู';
    }
  });
}

// ─── Stop Connector ───────────────────────────────────────────────────────────

document.getElementById('btn-stop-connector').addEventListener('click', async () => {
  const btn = document.getElementById('btn-stop-connector');
  setLoading(btn, true, 'Stopping...');
  try {
    await apiFetch('/api/connector/stop', { method: 'POST' });
    updateBadge('ngrok', 'disconnected');
    updateCard('ngrok', 'disconnected');
    updateStatusRow('ngrok', 'disconnected');
    updateChip('ngrok', 'disconnected');
    updateStatusRow('hub', 'offline', 'ออฟไลน์');
    updateOnlineBar(false);
    updateConnectAllButton(false);
    updateStopConnectorButton(false);
    document.getElementById('mcp-url-box').style.display = 'none';
    toast('Connector stopped', 'info');
  } catch (err) {
    toast(`Error: ${err.message}`, 'error');
  } finally {
    setLoading(btn, false);
  }
});

// ─── Connect All ──────────────────────────────────────────────────────────────

document.getElementById('btn-connect-all').addEventListener('click', async () => {
  const btn = document.getElementById('btn-connect-all');
  let ngrokToken  = document.getElementById('ngrok-token').value.trim();
  let ngrokDomain = document.getElementById('ngrok-domain').value.trim();

  if (/^.{4}x{6,}.{4}$/.test(ngrokToken)) {
    try {
      const preview = await apiFetch('/api/credentials/ngrok/preview?reveal=true');
      if (preview.has_credentials && preview.value) ngrokToken = preview.value;
    } catch (_) {}
  }

  setLoading(btn, true, 'Connecting...');
  let hubOnline = false;

  try {
    const data = await apiFetch('/api/connect-all', {
      method: 'POST',
      body: JSON.stringify({
        ngrok_authtoken: ngrokToken,
        ngrok_domain:    ngrokDomain,
      }),
    });

    const results = data.results || {};

    for (const svc of ['gsc', 'ga4', 'ahrefs', 'ngrok']) {
      if (results[svc]) {
        const status = results[svc].status;
        updateBadge(svc, status);
        updateCard(svc, status);
        updateStatusRow(svc, status);
        updateChip(svc, status);
        if (svc === 'ahrefs' && status === 'connected') loadAhrefsPreview(false);
        if (svc === 'ngrok' && status === 'connected') loadNgrokPreview(false);
      }
    }

    if (results.mcp_hub) {
      const hubStatus = results.mcp_hub.status;
      hubOnline = hubStatus === 'online';
      updateStatusRow('hub', hubStatus, hubOnline ? 'ออนไลน์' : (results.mcp_hub.message || 'ออฟไลน์'));
      updateOnlineBar(hubOnline);
    }

    if (data.mcp_url) {
      showMcpUrl(data.mcp_url);
      toast(`MCP Hub is ONLINE — URL copied to clipboard`, 'success', 5000);
      navigator.clipboard.writeText(data.mcp_url).catch(() => {});
    } else if (!data.ok) {
      toast('Some services failed. Check status panel.', 'error');
    }
  } catch (err) {
    toast(`Connect failed: ${err.message}`, 'error');
  } finally {
    setLoading(btn, false);
    updateConnectAllButton(hubOnline);
    updateStopConnectorButton(hubOnline);
  }
});

// ─── Refresh buttons ──────────────────────────────────────────────────────────

function doRefresh() {
  window.location.reload();
}

document.getElementById('btn-refresh').addEventListener('click', doRefresh);
document.getElementById('btn-refresh-2').addEventListener('click', doRefresh);

// ─── Delete All ───────────────────────────────────────────────────────────────

document.getElementById('btn-delete-all').addEventListener('click', () => {
  document.getElementById('confirm-overlay').style.display = 'flex';
});

document.getElementById('confirm-cancel').addEventListener('click', () => {
  document.getElementById('confirm-overlay').style.display = 'none';
});

document.getElementById('confirm-ok').addEventListener('click', async () => {
  document.getElementById('confirm-overlay').style.display = 'none';
  try {
    await apiFetch('/api/credentials', { method: 'DELETE' });
    toast('All credentials deleted', 'info');

    for (const svc of ['gsc', 'ga4', 'ahrefs', 'ngrok', 'hub']) {
      updateBadge(svc, 'disconnected');
      updateCard(svc, 'disconnected');
      updateStatusRow(svc, 'disconnected');
      updateChip(svc, 'disconnected');
      if (svc === 'gsc' || svc === 'ga4') {
        updateUploadFilename(svc, null);
        updateConnectButton(svc, 'disconnected');
      }
    }
    updateOnlineBar(false);
    updateConnectAllButton(false);
    updateStopConnectorButton(false);
    document.getElementById('mcp-url-box').style.display = 'none';
    document.getElementById('ahrefs-key').value = '';
    document.getElementById('ngrok-token').value = '';
    document.getElementById('ngrok-domain').value = '';
  } catch (err) {
    toast(`Error: ${err.message}`, 'error');
  }
});

// Close overlay on background click
document.getElementById('confirm-overlay').addEventListener('click', (e) => {
  if (e.target === e.currentTarget) {
    e.currentTarget.style.display = 'none';
  }
});

// ─── Copy MCP URL ─────────────────────────────────────────────────────────────

document.getElementById('copy-url-btn').addEventListener('click', () => {
  const url = document.getElementById('mcp-url-text').textContent;
  if (url && url !== '—') {
    navigator.clipboard.writeText(url)
      .then(() => toast('MCP URL copied!', 'success', 2000))
      .catch(() => toast('Could not copy URL', 'error'));
  }
});

// ─── Init ─────────────────────────────────────────────────────────────────────

function init() {
  setupFileUpload('gsc');
  setupFileUpload('ga4');
  setupOAuthButton('gsc');
  setupOAuthButton('ga4');
  setupDisconnect('gsc');
  setupDisconnect('ga4');
  setupDisconnect('ahrefs');
  setupDisconnect('ngrok');
  setupAhrefs();
  setupNgrok();

  // Initial status load
  refreshStatus();

  // Auto-refresh every 30 seconds
  setInterval(refreshStatus, 30_000);

  // Connector log refresh every 10 seconds
  setInterval(refreshConnectorLog, 10_000);
}

init();
