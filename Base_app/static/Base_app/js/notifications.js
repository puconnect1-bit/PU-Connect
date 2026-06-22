/**
 * PU-Connect — In-app notification bell
 *
 * Expects in the page:
 *   - An element with id="notifBtn"  (the bell button)
 *   - An element with id="notifDot"  (the red badge dot, hidden by default)
 *
 * Injects a dropdown panel (#notifPanel) after the button on first open.
 * Works on any page. Call initNotifications() after DOMContentLoaded.
 */

(function () {
  'use strict';

  const POLL_MS    = 30000; // refresh every 30 s while page is open
  const API_LIST   = '/chat/api/notifications/';
  const API_MARK   = '/chat/api/notifications/mark-read/';

  let _panel       = null;
  let _open        = false;
  let _pollTimer   = null;

  function csrf() {
    const m = document.cookie.match(/csrftoken=([^;]+)/);
    return m ? m[1] : '';
  }

  function esc(s) {
    const d = document.createElement('div');
    d.textContent = String(s || '');
    return d.innerHTML;
  }

  function timeLabel(str) {
    // str is already formatted by Django (e.g. "20 Jun, 02:15 PM")
    return str;
  }

  /* ── Fetch & render ── */
  async function fetchNotifications() {
    try {
      const res  = await fetch(API_LIST, { credentials: 'same-origin' });
      if (!res.ok) return;
      const data = await res.json();
      updateDot(data.unread_count);
      if (_open && _panel) renderPanel(data.notifications);
    } catch (e) { /* silent */ }
  }

  function updateDot(count) {
    const dot = document.getElementById('notifDot');
    if (!dot) return;
    if (count > 0) {
      dot.textContent = count > 9 ? '9+' : String(count);
      dot.style.display = '';
    } else {
      dot.style.display = 'none';
    }
  }

  function renderPanel(items) {
    if (!_panel) return;
    const list = _panel.querySelector('.np-list');
    if (!list) return;

    if (!items || !items.length) {
      list.innerHTML = '<div class="np-empty">No notifications yet</div>';
      return;
    }

    list.innerHTML = items.map(n => `
      <a class="np-item${n.is_read ? '' : ' np-unread'}" href="${esc(n.link) || '/chat/'}" onclick="npMarkOne(${n.id}, this)">
        <span class="np-icon ${esc(n.type)}">${n.type === 'message' ? svgMsg() : svgSys()}</span>
        <span class="np-body">
          <span class="np-title">${esc(n.title)}</span>
          <span class="np-content">${esc(n.content)}</span>
          <span class="np-time">${esc(n.created_at)}</span>
        </span>
        ${n.is_read ? '' : '<span class="np-badge"></span>'}
      </a>`).join('');
  }

  /* ── Panel DOM ── */
  function buildPanel() {
    const btn = document.getElementById('notifBtn');
    if (!btn) return;

    const panel = document.createElement('div');
    panel.id        = 'notifPanel';
    panel.className = 'notif-panel';
    panel.innerHTML = `
      <div class="np-head">
        <span class="np-heading">Notifications</span>
        <button class="np-mark-all" onclick="npMarkAll()">Mark all read</button>
      </div>
      <div class="np-list"><div class="np-empty">Loading…</div></div>`;

    // Append after bell button's parent or to body
    const anchor = btn.closest('header, nav, .top-bar, .dtp-bar, .pub-bar') || document.body;
    anchor.style.position = anchor.style.position || 'relative';
    anchor.appendChild(panel);

    // Close on outside click
    document.addEventListener('click', function outsideClick(e) {
      if (!panel.contains(e.target) && e.target !== btn && !btn.contains(e.target)) {
        closePanel();
      }
    }, true);

    _panel = panel;
  }

  function openPanel() {
    if (!_panel) buildPanel();
    _panel.classList.add('np-open');
    _open = true;
    // Mark all read on open after a short delay
    setTimeout(() => {
      markAllRead();
    }, 1000);
    // Fetch fresh data immediately
    fetchNotifications();
  }

  function closePanel() {
    if (_panel) _panel.classList.remove('np-open');
    _open = false;
  }

  function togglePanel() {
    if (_open) closePanel();
    else       openPanel();
  }

  /* ── Mark read ── */
  async function markAllRead() {
    try {
      await fetch(API_MARK, {
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'X-CSRFToken': csrf(), 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      });
      updateDot(0);
    } catch (e) { /* silent */ }
  }

  /* Exposed globally so inline onclick in rendered items can call it */
  window.npMarkAll = function () {
    markAllRead();
    if (_panel) {
      const items = _panel.querySelectorAll('.np-unread');
      items.forEach(el => {
        el.classList.remove('np-unread');
        const badge = el.querySelector('.np-badge');
        if (badge) badge.remove();
      });
    }
  };

  window.npMarkOne = function (id, el) {
    fetch(API_MARK, {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'X-CSRFToken': csrf(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ id }),
    }).catch(() => {});
    if (el) {
      el.classList.remove('np-unread');
      const badge = el.querySelector('.np-badge');
      if (badge) badge.remove();
    }
  };

  /* ── SVG icons ── */
  function svgMsg() {
    return '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>';
  }
  function svgSys() {
    return '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>';
  }

  /* ── Init ── */
  window.initNotifications = function () {
    const btn = document.getElementById('notifBtn');
    if (!btn) return;

    btn.addEventListener('click', function (e) {
      e.stopPropagation();
      togglePanel();
    });

    // Initial fetch
    fetchNotifications();

    // Poll
    _pollTimer = setInterval(fetchNotifications, POLL_MS);
  };

  // Auto-init
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', window.initNotifications);
  } else {
    window.initNotifications();
  }
})();
