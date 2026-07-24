/* ============================================================
   CONTEXT MENU & MESSAGE ACTIONS
   ============================================================ */

/**
 * Open the context menu for a message.
 * @param {Event} e - Click event.
 * @param {number} idx - Message index.
 * @param {number|string} cid - Conversation ID.
 */
function openCtxMenu(e, idx, cid) {
  e.stopPropagation();
  ctxMsgIdx = idx;
  ctxMsgCid = cid;
  const m = msgs[cid][idx];
  const menu = document.getElementById('ctxMenu');
  const ov = document.getElementById('ctxOverlay');

  // Show Edit only for own text messages
  document.getElementById('ctxEdit').style.display =
    (m.from === 'out' && m.text && !m.voice && !m.images && !m.offer && !m.meetup) ? 'flex' : 'none';
  // Update pin label
  const pinItem = document.getElementById('ctxPin');
  pinItem.childNodes[pinItem.childNodes.length - 1].textContent = m.pinned ? ' Unpin' : ' Pin';

  menu.style.display = 'block';
  ov.style.display = 'block';

  // Position near tap, clamped to viewport
  const vw = window.innerWidth, vh = window.innerHeight;
  menu.style.left = '0';
  menu.style.top = '0';
  const mw = menu.offsetWidth || 190, mh = menu.offsetHeight || 200;
  let x = e.clientX, y = e.clientY;
  if (x + mw > vw - 8) x = vw - mw - 8;
  if (y + mh > vh - 8) y = vh - mh - 8;
  if (x < 8) x = 8;
  if (y < 8) y = 8;
  menu.style.left = x + 'px';
  menu.style.top = y + 'px';

  document.querySelectorAll('.msg-wrap.ctx-open').forEach(w => w.classList.remove('ctx-open'));
  const wrap = document.querySelector(`.msg-wrap[data-idx="${idx}"][data-cid="${cid}"]`);
  if (wrap) wrap.classList.add('ctx-open');
}

/**
 * Close the context menu.
 */
function closeCtxMenu() {
  document.getElementById('ctxMenu').style.display = 'none';
  document.getElementById('ctxOverlay').style.display = 'none';
  document.querySelectorAll('.msg-wrap.ctx-open').forEach(w => w.classList.remove('ctx-open'));
  ctxMsgIdx = null;
  ctxMsgCid = null;
}

/**
 * Execute a context menu action.
 * @param {string} action - The action name: 'reply', 'copy', 'pin', 'edit', 'delete'.
 */
function ctxAction(action) {
  const idx = ctxMsgIdx, cid = ctxMsgCid;
  closeCtxMenu();
  if (idx === null || !cid) return;
  const m = msgs[cid][idx];
  if (!m) return;

  if (action === 'reply') {
    startReply(idx, cid);
  } else if (action === 'copy') {
    const text = m.text || (m.voice ? '[Voice note]' : m.images ? '[Photo]' : '[Message]');
    navigator.clipboard.writeText(text)
      .then(() => showToast('Copied to clipboard'))
      .catch(() => {
        const ta = document.createElement('textarea');
        ta.value = text;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
        showToast('Copied to clipboard');
      });
  } else if (action === 'pin') {
    const wasPinned = m.pinned;
    msgs[cid].forEach(msg => msg.pinned = false);
    if (!wasPinned) {
      m.pinned = true;
      const preview = m.text || (m.voice ? 'Voice note' : m.images ? 'Photo' : 'Message');
      document.getElementById('pinnedBarText').textContent = preview;
      const pb = document.getElementById('pinnedBar');
      pb.classList.add('show');
      pb.dataset.idx = idx;
      showToast('Message pinned');
    } else {
      document.getElementById('pinnedBar').classList.remove('show');
      showToast('Message unpinned');
    }
    renderMsgs(cid);
  } else if (action === 'edit') {
    if (!m.text) return;
    const inp = document.getElementById('msgInput');
    inp.value = m.text;
    autoResize(inp);
    toggleSend();
    inp.focus();
    inp.dataset.editIdx = idx;
    inp.dataset.editCid = cid;
    document.getElementById('sendBtn').innerHTML =
      '<svg viewBox="0 0 24 24" style="width:16px;height:16px;stroke:#0d0e11;fill:none;stroke-width:2.5;stroke-linecap:round;stroke-linejoin:round"><polyline points="20 6 9 17 4 12"/></svg>';
    showToast('Editing — press Enter to save');
  } else if (action === 'delete') {
    showDeleteSubmenu(idx, cid, m);
  } else if (action === 'delete_for_me') {
    msgs[cid].splice(idx, 1);
    renderMsgs(cid);
    showToast('Message deleted');
  } else if (action === 'delete_for_everyone') {
    if (chatSocket && chatSocket.readyState === WebSocket.OPEN && m.id) {
      chatSocket.send(JSON.stringify({ type: 'delete', message_id: m.id }));
      m.is_deleted = true;
      renderMsgs(cid);
      showToast('Message deleted for everyone');
    } else {
      showToast('Cannot delete — not connected or message not saved');
    }
  }
}

/**
 * Show a submenu with delete options.
 * @param {number} idx - Message index.
 * @param {number|string} cid - Conversation ID.
 * @param {object} m - Message object.
 */
function showDeleteSubmenu(idx, cid, m) {
  const existing = document.getElementById('deleteSubmenu');
  if (existing) existing.remove();

  const submenu = document.createElement('div');
  submenu.id = 'deleteSubmenu';
  submenu.className = 'ctx-menu';
  submenu.style.display = 'block';
  submenu.style.left = '0';
  submenu.style.top = '0';

  // Position near the message
  const wrap = document.querySelector(`.msg-wrap[data-idx="${idx}"][data-cid="${cid}"]`);
  if (wrap) {
    const rect = wrap.getBoundingClientRect();
    submenu.style.left = (rect.right + 10) + 'px';
    submenu.style.top = rect.top + 'px';
  }

  submenu.innerHTML = `
    <div class="ctx-item" onclick="ctxAction('delete_for_me');closeDeleteSubmenu();">
      <svg viewBox="0 0 24 24"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4h6v2"/></svg>
      Delete for me
    </div>
    <div class="ctx-item" onclick="ctxAction('delete_for_everyone');closeDeleteSubmenu();">
      <svg viewBox="0 0 24 24"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4h6v2"/></svg>
      Delete for everyone
    </div>
  `;

  document.body.appendChild(submenu);

  const overlay = document.createElement('div');
  overlay.id = 'deleteSubmenuOverlay';
  overlay.className = 'ctx-overlay';
  overlay.style.display = 'block';
  overlay.onclick = closeDeleteSubmenu;
  document.body.appendChild(overlay);
}

function closeDeleteSubmenu() {
  const submenu = document.getElementById('deleteSubmenu');
  const overlay = document.getElementById('deleteSubmenuOverlay');
  if (submenu) submenu.remove();
  if (overlay) overlay.remove();
}