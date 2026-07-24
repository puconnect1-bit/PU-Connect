/* ============================================================
   CHAT APPLICATION — INITIALIZATION ENTRY POINT
   ============================================================ */

/**
 * Main application initialisation.
 * Fetches conversations, handles pending chat opens,
 * and connects presence/WebSocket.
 */
async function init() {
  await fetchConversations();

  // Opened from "Message Seller" on detail page
  const openConvId = sessionStorage.getItem('pu-open-conv');
  if (openConvId) {
    sessionStorage.removeItem('pu-open-conv');
    const conv = CONVS.find(c => String(c.id) === String(openConvId));
    if (conv) { openConv(conv); connectPresence(); return; }
    await fetchConversations();
    const conv2 = CONVS.find(c => String(c.id) === String(openConvId));
    if (conv2) { openConv(conv2); connectPresence(); return; }
  }

  // Opened from reels / other pages via localStorage
  const pendingChat = localStorage.getItem('pu-chat-open');
  if (pendingChat) {
    localStorage.removeItem('pu-chat-open');
    try {
      const parsed = JSON.parse(pendingChat);
      const { username } = parsed;
      if (username) {
        const csrf = document.cookie.split('; ').find(r => r.startsWith('csrftoken='))?.split('=')[1] || '';
        const res = await fetch('/chat/api/start-direct/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
          body: JSON.stringify({ username }),
        });
        if (res.ok) {
          const d = await res.json();
          if (d.status === 'success') {
            await fetchConversations();
            const conv = CONVS.find(c => String(c.id) === String(d.conv_id));
            if (conv) { openConv(conv); connectPresence(); return; }
            const stub = {
              id: d.conv_id,
              name: parsed.listing || username,
              username: username,
              avatar_url: '',
              listing: parsed.listing || 'General',
              listingEmoji: '💬',
              price: '',
              time: 'Now',
              badge: 0,
              type: 'direct',
              status: 'away',
              _other_user_id: null,
              blocked: false,
            };
            CONVS.unshift(stub);
            openConv(stub);
            connectPresence();
            return;
          }
        }
      }
    } catch (e) { console.error('pu-chat-open error', e); }
  }

  // Connect presence socket
  connectPresence();

  // On desktop, auto-open first conversation
  if (window.innerWidth >= 768 && CONVS.length > 0) openConv(CONVS[0]);
}

/**
 * Helper to set an active navigation indicator.
 * @param {HTMLElement} el - The element to mark active.
 */
function setNi(el) {
  document.querySelectorAll('.ni').forEach(i => i.classList.remove('on'));
  el.classList.add('on');
}

/* ---- RESIZE HANDLER ---- */
window.addEventListener('resize', () => {
  if (window.innerWidth >= 768) {
    document.getElementById('leftPanel').classList.remove('hidden');
    document.getElementById('rightPanel').classList.remove('visible');
    if (!activeConv && CONVS.length > 0) openConv(CONVS[0]);
  }
});

/* ---- START ---- */
document.addEventListener('DOMContentLoaded', init);

// Show own online dot in the header
(function () {
  const logo = document.querySelector('.left-logo');
  if (!logo) return;
  const dot = document.createElement('span');
  dot.style.cssText = 'display:inline-block;width:7px;height:7px;border-radius:50%;background:#22c55e;margin-left:.4rem;vertical-align:middle;flex-shrink:0';
  logo.appendChild(dot);
})();