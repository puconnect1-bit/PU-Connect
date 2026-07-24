/* ============================================================
   CHAT UTILITY FUNCTIONS
   ============================================================ */

/**
 * Escape HTML special characters to prevent XSS.
 * @param {*} s - The value to escape.
 * @returns {string} Escaped string.
 */
function escHtml(s) {
  if (s === null || s === undefined) return '';
  return String(s).replace(/&/g, '&').replace(/</g, '<').replace(/>/g, '>');
}

/**
 * Show a brief toast notification at the bottom of the screen.
 * @param {string} msg - The message to display.
 */
let toastTimer;
function showToast(msg) {
  const t = document.getElementById('toast');
  if (!t) return;
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.remove('show'), 2800);
}

/**
 * Modern confirm dialog overlay.
 * @param {string} msg - HTML message content.
 * @param {Function} onYes - Callback when user clicks Confirm.
 * @param {object} [opts] - Options { icon, okLabel, danger }.
 */
function puConfirm(msg, onYes, opts = {}) {
  const ov = document.getElementById('puDlgOv');
  if (!ov) return;
  document.getElementById('puDlgMsg').innerHTML = msg;
  document.getElementById('puDlgIcon').textContent = opts.icon || '';
  const ok = document.getElementById('puDlgOk');
  ok.textContent = opts.okLabel || 'Confirm';
  ok.style.background = opts.danger ? '#e53e3e' : 'var(--teal,#00a884)';
  ok.style.color = '#fff';
  ov.classList.add('show');
  const close = () => ov.classList.remove('show');
  ok.onclick = () => { close(); onYes(); };
  document.getElementById('puDlgCancel').onclick = close;
  ov.onclick = (e) => { if (e.target === ov) close(); };
}

/**
 * Auto-resize a textarea to fit its content.
 * @param {HTMLTextAreaElement} el
 */
function autoResize(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}

/**
 * Toggle send / mic button visibility based on input content.
 */
function toggleSend() {
  const inp = document.getElementById('msgInput');
  const sendBtn = document.getElementById('sendBtn');
  const micBtn = document.getElementById('micBtn');
  if (!inp || !sendBtn || !micBtn) return;
  const v = inp.value.trim();
  sendBtn.style.display = v ? 'flex' : 'none';
  micBtn.style.display = v ? 'none' : 'flex';
  sendBtn.disabled = !v;
}

/**
 * Upload a file to R2 storage via the backend API.
 * @param {File|Blob} file - The file to upload.
 * @param {string} [resourceType='image'] - 'image' or 'voice'.
 * @returns {Promise<string>} The public URL of the uploaded file.
 */
async function uploadToR2(file, resourceType) {
  resourceType = resourceType || 'image';
  const csrf = document.cookie.split('; ').find(r => r.startsWith('csrftoken='))?.split('=')[1];
  const fd = new FormData();
  fd.append('file', file);
  fd.append('resource_type', resourceType);
  const res = await fetch('/api/r2-upload/', {
    method: 'POST',
    headers: { 'X-CSRFToken': csrf },
    body: fd,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error || 'Upload failed');
  }
  const { public_url } = await res.json();
  return public_url;
}

/**
 * Get the first supported MIME type for MediaRecorder.
 * @returns {string} Supported MIME type or empty string.
 */
function getSupportedMime() {
  const types = [
    'audio/webm;codecs=opus',
    'audio/webm',
    'audio/ogg;codecs=opus',
    'audio/ogg',
    'audio/mp4;codecs=mp4a.40.2',
    'audio/mp4',
  ];
  return types.find(t => {
    try { return MediaRecorder.isTypeSupported(t); } catch { return false; }
  }) || '';
}

/**
 * Format seconds into mm:ss duration string.
 * @param {number} secs
 * @returns {string}
 */
function fmtDur(secs) {
  const s = Math.max(0, Math.round(secs));
  return Math.floor(s / 60) + ':' + (s % 60).toString().padStart(2, '0');
}

/**
 * Generate a flat-ish waveform array for placeholder use.
 * @param {number} n - Number of bars.
 * @returns {number[]}
 */
function generateFlatWaveform(n) {
  return Array.from({ length: n }, (_, i) =>
    Math.round(5 + Math.sin(i / 2.5) * 4 + Math.random() * 6)
  );
}