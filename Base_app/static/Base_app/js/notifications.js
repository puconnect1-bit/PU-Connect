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

  const API_LIST       = '/chat/api/notifications/';
  const API_MARK       = '/chat/api/notifications/mark-read/';
  const FALLBACK_MS    = 60000; // slow safety net used only when the socket is down
  const NOTIF_WS       = (window.location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host + '/ws/notifications/';

  let _panel           = null;
  let _open            = false;
  let _ws              = null;
  let _wsRetryTimer    = null;
  let _fallbackTimer   = null;

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

  function updateChatBadge(count) {
    const badge = document.getElementById('bnChatBadge');
    if (!badge) return;
    if (count > 0) {
      badge.textContent = count > 9 ? '9+' : String(count);
      badge.style.display = 'flex';
    } else {
      badge.style.display = 'none';
    }
  }

  function onNotificationWSMessage(e) {
    let data;
    try { data = JSON.parse(e.data); } catch (err) { return; }
    if (data.type === 'notification') {
      updateDot(data.unread_count != null ? data.unread_count : 0);
      if (_open && _panel) fetchNotifications();
    } else if (data.type === 'unread_count') {
      updateChatBadge(data.unread_count || 0);
    }
  }

  function connectNotifications() {
    if (!window.WebSocket) return;
    if (_ws && (_ws.readyState === WebSocket.OPEN || _ws.readyState === WebSocket.CONNECTING)) return;
    try {
      _ws = new WebSocket(NOTIF_WS);
    } catch (err) {
      scheduleWSReconnect();
      return;
    }
    _ws.onmessage = onNotificationWSMessage;
    _ws.onopen = function () {
      if (_wsRetryTimer) { clearTimeout(_wsRetryTimer); _wsRetryTimer = null; }
    };
    _ws.onclose = function () { _ws = null; scheduleWSReconnect(); };
    _ws.onerror = function () { try { _ws.close(); } catch (err) {} };
  }

  function scheduleWSReconnect() {
    if (_wsRetryTimer) return;
    const timer = setTimeout(function () {
      _wsRetryTimer = null;
      if (document.visibilityState !== 'hidden') connectNotifications();
    }, 5000);
    _wsRetryTimer = timer;
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

    // Append to body and use fixed positioning for reliable display on all pages
    document.body.appendChild(panel);

    // Position the panel relative to the bell button
    function positionPanel() {
      const rect = btn.getBoundingClientRect();
      panel.style.position = 'fixed';
      panel.style.top = (rect.bottom + 8) + 'px';
      panel.style.right = (window.innerWidth - rect.right) + 'px';
      panel.style.left = 'auto';
      panel.style.bottom = 'auto';
    }

    // Reposition on scroll and resize
    positionPanel();
    window.addEventListener('scroll', positionPanel, { passive: true });
    window.addEventListener('resize', positionPanel, { passive: true });

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

    // Initial fetch (populates state before the socket delivers anything)
    fetchNotifications();

    // Live updates via WebSocket — no more 10s HTTP polling
    connectNotifications();

    // Slow safety-net poll: only while the tab is visible AND the socket is down
    _fallbackTimer = setInterval(function () {
      if (document.visibilityState === 'hidden') return;
      if (_ws && _ws.readyState === WebSocket.OPEN) return;
      fetchNotifications();
    }, FALLBACK_MS);

    // Refresh state whenever the tab becomes visible again
    document.addEventListener('visibilitychange', function () {
      if (document.visibilityState === 'visible') {
        fetchNotifications();
        if (!_ws || _ws.readyState !== WebSocket.OPEN) connectNotifications();
      }
    });
  };

  // Auto-init
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', window.initNotifications);
  } else {
    window.initNotifications();
  }
})();
