/* ============================================================
   MESSAGE RENDERING & SENDING
   ============================================================ */

/**
 * Fetch messages for a conversation from the API.
 * @param {number|string} cid - Conversation ID.
 */
async function fetchMessages(cid) {
  try {
    const res = await fetch(`/chat/api/messages/${cid}/`);
    msgs[cid] = await res.json();
    // Populate vnAudioMap for server-side voice notes
    (msgs[cid] || []).forEach(m => {
      if (m.voice_url && m.id) {
        const stableId = 'srv-' + cid + '-' + m.id;
        vnAudioMap[stableId] = {
          url: m.voice_url,
          duration: m.voice_duration || 0,
          waveform: generateFlatWaveform(28),
        };
      }
    });
    renderMsgs(cid);
  } catch (e) {
    console.error('Failed to fetch messages', e);
  }
}

/**
 * Render messages for a given conversation into the message area.
 * @param {number|string} cid - Conversation ID.
 */
function renderMsgs(cid) {
  const area = document.getElementById('msgArea');
  if (!area) return;
  const list = msgs[cid] || [];
  let lastDate = '';
  area.innerHTML = '';

  // System message at top
  const sys = document.createElement('div');
  sys.className = 'sys-msg';
  sys.textContent = 'All messages are end-to-end encrypted on campus';
  area.appendChild(sys);

  list.forEach((m, idx) => {
    // Date separator
    const timeStr = m.time || '';
    const datePart = timeStr.includes('Yesterday') ? 'Yesterday'
      : timeStr.includes('Mon') ? 'Monday'
      : timeStr.includes('Sun') ? 'Sunday' : 'Today';
    if (datePart !== lastDate) {
      lastDate = datePart;
      const sep = document.createElement('div');
      sep.className = 'date-sep';
      sep.innerHTML = `<span>${datePart}</span>`;
      area.appendChild(sep);
    }

    const wrap = document.createElement('div');
    wrap.className = `msg ${m.from} msg-wrap`;
    wrap.dataset.idx = idx;
    wrap.dataset.cid = cid;
    if (m.pinned) wrap.id = `pinmsg-${cid}-${idx}`;

    // -- Action button --
    const actionBtn = `<button class="msg-action-btn" onclick="openCtxMenu(event,${idx},'${cid}')" title="Message options"><svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor"><circle cx="12" cy="5" r="1.5"/><circle cx="12" cy="12" r="1.5"/><circle cx="12" cy="19" r="1.5"/></svg></button>`;

    // -- Reply quote --
    let replyQuote = '';
    if (m.reply_to && m.reply_to_name && m.reply_to_text) {
      replyQuote = `<div class="reply-quote" onclick="scrollToReply('${cid}','${m.reply_to}')">
        <div class="reply-quote-name">${escHtml(m.reply_to_name)}</div>
        <div>${escHtml(String(m.reply_to_text).slice(0, 80))}${m.reply_to_text.length > 80 ? '…' : ''}</div>
      </div>`;
    } else if (m.replyTo !== undefined && msgs[cid][m.replyTo]) {
      const orig = msgs[cid][m.replyTo];
      const origText = orig.text || (orig.voice ? 'Voice note' : orig.images ? 'Photo' : '…');
      replyQuote = `<div class="reply-quote" onclick="scrollToMsg(${m.replyTo},'${cid}')">
        <div class="reply-quote-name">${orig.from === 'out' ? 'You' : activeConv?.name || 'Them'}</div>
        <div>${escHtml(String(origText).slice(0, 80))}${origText.length > 80 ? '…' : ''}</div>
      </div>`;
    }

    // -- Pinned indicator --
    const pinnedTag = m.pinned ? `<div class="pinned-indicator">Pinned</div>` : '';

    // -- Edited tag --
    const editedTag = m.edited ? `<span class="edited-tag">(edited)</span>` : '';

    let meetupHTML = '';
    if (m.meetup_spot) {
      meetupHTML = `<div class="meetup-card">
        <div style="font-size:1.1rem;margin-bottom:.3rem">Meetup Scheduled</div>
        <div><strong>Location:</strong> ${escHtml(m.meetup_spot)}</div>
        <div><strong>Time:</strong> ${escHtml(m.meetup_time)}</div>
      </div>`;
    }

    let inner;

    // -- Deleted message --
    if (m.is_deleted) {
      inner = `<div class="bubble deleted-msg">${m.from === 'out' ? 'You deleted this message' : 'This message was deleted'}</div>`;
    }
    // -- Offer card --
    else if (m.offer) {
      const isPending = m.offer.status === 'pending';
      const isDeclined = m.offer.status === 'declined';
      const isAccepted = m.offer.status === 'accepted';
      inner = `${actionBtn}<div class="bubble">${replyQuote}
        ${m.text ? `<div>${escHtml(m.text)}</div>` : ''}
        <div class="offer-card">
          <div class="offer-label">Price Offer</div>
          <div class="offer-amount">${m.offer.amount}</div>
          <div class="offer-item">${m.offer.item}</div>
          ${isPending && m.from === 'in'
            ? `<div class="offer-btns"><button class="offer-btn accept" onclick="acceptOffer(this,'${cid}')">✅ Accept</button><button class="offer-btn decline" onclick="declineOffer(this)">❌ Decline</button></div>`
            : ''}
          ${isAccepted ? '<div class="offer-accepted">Offer accepted</div>' : ''}
          ${isDeclined ? '<div style="font-size:.74rem;color:var(--red);margin-top:.4rem">❌ Offer declined</div>' : ''}
        </div>
      </div>`;
    }
    // -- Meetup card --
    else if (m.meetup_spot) {
      inner = `${actionBtn}<div class="bubble">${replyQuote}
        ${m.text ? `<div>${escHtml(m.text)}</div>` : ''}
        <div class="meetup-card">
          <div class="meetup-label">Meetup Arranged</div>
          <div class="meetup-row"><span class="meetup-ico">📍</span><span>${escHtml(m.meetup_spot)}</span></div>
          <div class="meetup-row"><span class="meetup-ico">🕐</span><span>${escHtml(m.meetup_time)}</span></div>
        </div>
      </div>`;
    }
    // -- Images --
    else if (m.images) {
      const imgs = m.images;
      const imgHTML = imgs.length === 1
        ? `<div class="img-bubble" onclick="previewFullImg('${imgs[0]}')"><img src="${imgs[0]}" alt="photo"/></div>`
        : `<div class="img-bubble-grid${imgs.length >= 2 ? ' cols2' : ''}">${imgs.map(src =>
            `<img src="${src}" alt="photo" onclick="previewFullImg('${src}')">`).join('')}</div>`;
      inner = `${actionBtn}${replyQuote}${imgHTML}`;
    }
    // -- Voice note --
    else if (m.voice || m.voice_url) {
      inner = renderVoiceBubble(m, idx, cid, actionBtn, replyQuote);
    }
    // -- System message --
    else if (m.from === 'system') {
      const pill = document.createElement('div');
      pill.className = 'sys-msg';
      pill.textContent = m.text || '';
      area.appendChild(pill);
      return;
    }
    // -- Normal text message --
    else {
      inner = `${actionBtn}<div class="bubble" id="msg-${cid}-${idx}">${replyQuote}${meetupHTML}${m.image_url
        ? `<div class="img-bubble" onclick="previewFullImg('${m.image_url}')"><img src="${m.image_url}" alt="photo"/></div>`
        : ''}${m.voice_url ? `<div class="msg-voice">Voice Note</div>` : ''}${escHtml(m.text || '')}${editedTag}</div>`;
    }

    // WhatsApp-style ticks
    let tickHTML = '';
    if (m.from === 'out') {
      if (m.pending) {
        tickHTML = `<span class="msg-tick pending"><svg width="12" height="11" viewBox="0 0 12 11" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M1.5 5.5L4.5 8.5L10.5 2.5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg></span>`;
      } else if (m.is_read) {
        tickHTML = `<span class="msg-tick read"><svg width="16" height="11" viewBox="0 0 16 11" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M1 5.5L4 8.5L10 2.5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/><path d="M5 5.5L8 8.5L14 2.5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg></span>`;
      } else {
        tickHTML = `<span class="msg-tick delivered"><svg width="16" height="11" viewBox="0 0 16 11" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M1 5.5L4 8.5L10 2.5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/><path d="M5 5.5L8 8.5L14 2.5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg></span>`;
      }
    }

    inner += `${pinnedTag}<div class="msg-meta"><span class="msg-time">${m.time}</span>${tickHTML}</div>`;
    wrap.innerHTML = inner;

    // Add swipe-to-reply touch handlers
    wrap.addEventListener('touchstart', handleTouchStart, { passive: true });
    wrap.addEventListener('touchmove', handleTouchMove, { passive: false });
    wrap.addEventListener('touchend', handleTouchEnd);

    area.appendChild(wrap);
  });

  area.scrollTop = area.scrollHeight;
}

/**
 * Build the HTML for a voice note bubble.
 * @param {object} m - Message object.
 * @param {number} idx - Message index.
 * @param {number|string} cid - Conversation ID.
 * @param {string} actionBtn - Action button HTML.
 * @param {string} replyQuote - Reply quote HTML.
 * @returns {string} Voice note bubble HTML.
 */
function renderVoiceBubble(m, idx, cid, actionBtn, replyQuote) {
  let id, url, duration, waveform;
  if (m.voice) {
    id = m.voice.stableId;
    url = m.voice.url;
    duration = m.voice.duration || 0;
    waveform = m.voice.waveform || [];
    if (id && url && !vnAudioMap[id])
      vnAudioMap[id] = { url, duration, waveform };
  } else {
    id = m.id ? 'srv-' + cid + '-' + m.id : 'srv-' + cid + '-' + idx;
    url = m.voice_url;
    duration = m.voice_duration || 0;
    waveform = m.voice_waveform || generateFlatWaveform(28);
    if (!vnAudioMap[id])
      vnAudioMap[id] = { url, duration, waveform };
  }

  const bars = vnAudioMap[id].waveform;
  const barHTML = bars.map(h => `<div class="vn-bar" style="height:${Math.max(3, h)}px"></div>`).join('');

  return `${actionBtn}<div class="vn-bubble">
    <button class="vn-play" id="play-${id}" onclick="playVoice('${id}')" title="Play / Pause">
      <svg viewBox="0 0 24 24"><polygon points="5 3 19 12 5 21 5 3"/></svg>
    </button>
    <div class="vn-info">
      <div class="vn-seek" id="seek-${id}" onclick="seekVoice(event,'${id}')" onmousemove="vnSeekHover(event,'${id}')" onmouseleave="vnSeekLeave('${id}')">
        <div class="vn-bars" id="bars-${id}">${barHTML}</div>
        <div class="vn-seek-tooltip" id="tip-${id}"></div>
      </div>
      <div class="vn-progress-wrap" id="pwrap-${id}" onclick="seekVoice(event,'${id}')">
        <div class="vn-progress" id="prog-${id}"></div>
        <div class="vn-progress-thumb" id="thumb-${id}"></div>
      </div>
      <div class="vn-footer">
        <span class="vn-dur" id="dur-${id}">${duration ? fmtDur(duration) : '0:00'}</span>
        <span class="vn-speed" id="spd-${id}" onclick="cycleSpeed('${id}')" title="Playback speed">1×</span>
      </div>
    </div>
  </div>`;
}

/* ============================================================
   MESSAGE SENDING
   ============================================================ */

/**
 * Send a text message (handles edit, reply, and normal send).
 */
function sendMessage() {
  const inp = document.getElementById('msgInput');
  const text = inp.value.trim();
  if (!text || !activeConv) return;

  // -- Edit mode --
  if (inp.dataset.editIdx !== undefined && inp.dataset.editIdx !== '') {
    const idx = parseInt(inp.dataset.editIdx);
    const cid = inp.dataset.editCid;
    if (msgs[cid] && msgs[cid][idx]) {
      msgs[cid][idx].text = text;
      msgs[cid][idx].edited = true;
    }
    inp.value = '';
    inp.style.height = '';
    delete inp.dataset.editIdx;
    delete inp.dataset.editCid;
    document.getElementById('sendBtn').innerHTML =
      '<svg viewBox="0 0 24 24" style="width:17px;height:17px;stroke:#0d0e11;fill:none;stroke-width:2.5;stroke-linecap:round;stroke-linejoin:round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>';
    toggleSend();
    renderMsgs(cid);
    renderConvList(document.getElementById('srchInput').value);
    return;
  }

  // -- Normal / reply send --
  const now = new Date();
  const time = now.toLocaleTimeString('en-GH', { hour: 'numeric', minute: '2-digit', hour12: true });
  const cid = activeConv.id;
  if (!msgs[cid]) msgs[cid] = [];

  // Optimistic push
  const optMsg = { from: 'out', text, time, pending: true };
  msgs[cid].push(optMsg);
  renderMsgs(cid);

  const msgObj = { message: text, image_url: null, voice_url: null };

  // Attach reply_to_id if replying
  if (replyIdx !== null && replyCid === cid) {
    const replyMsg = msgs[cid][replyIdx];
    if (replyMsg && replyMsg.id) {
      msgObj.reply_to_id = replyMsg.id;
    }
  }

  if (chatSocket && chatSocket.readyState === WebSocket.OPEN) {
    chatSocket.send(JSON.stringify(msgObj));
    cancelReply();
    inp.value = '';
    inp.style.height = '';
    toggleSend();
  } else {
    showToast('Not connected to chat server');
  }
}

/**
 * Handle keyboard events on the message input.
 * @param {KeyboardEvent} e
 */
function handleKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}

/**
 * Handle input change for typing indicator.
 */
function onInputChange() {
  const hasText = document.getElementById('msgInput').value.length > 0;
  if (hasText && !_typingSent) {
    _typingSent = true;
    sendTypingSignal(true);
  }
  clearTimeout(_typingStopTimer);
  if (hasText) {
    _typingStopTimer = setTimeout(() => { _typingSent = false; sendTypingSignal(false); }, 3000);
  } else {
    _typingSent = false;
    sendTypingSignal(false);
  }
}

/**
 * Insert an offer template into the message input.
 */
function insertOffer() {
  document.getElementById('msgInput').value = 'I\'d like to offer you ';
  autoResize(document.getElementById('msgInput'));
  toggleSend();
  document.getElementById('msgInput').focus();
}

/**
 * Start a reply to a specific message.
 * @param {number} idx - Message index.
 * @param {number|string} cid - Conversation ID.
 */
function startReply(idx, cid) {
  replyIdx = idx;
  replyCid = cid;
  const m = msgs[cid][idx];
  const name = m.from === 'out' ? 'You' : activeConv?.name || 'Them';
  const preview = m.text || (m.voice ? 'Voice note' : m.images ? 'Photo' : 'Message');
  document.getElementById('replyName').textContent = name;
  document.getElementById('replyText').textContent = preview;
  document.getElementById('replyBanner').classList.add('show');
  document.getElementById('msgInput').focus();
}

/**
 * Cancel the current reply.
 */
function cancelReply() {
  replyIdx = null;
  replyCid = null;
  document.getElementById('replyBanner').classList.remove('show');
}

/**
 * Open a conversation and render messages.
 * @param {object} c - Conversation object.
 */
function openConv(c) {
  if (!c) return;
  activeConv = c;

  // Clear badge
  const ci = CONVS.find(x => x.id === c.id);
  if (ci) ci.badge = 0;
  renderConvList(document.getElementById('srchInput').value);

  // Update header
  const chatAvEl = document.getElementById('chatAv');
  chatAvEl.className = 'chat-av';
  chatAvEl.innerHTML = c.avatar_url
    ? `<img src="${c.avatar_url}" alt="" style="width:100%;height:100%;object-fit:cover;border-radius:50%"/>`
    : AV_SVG;
  document.getElementById('chatName').textContent = c.name;
  const statusEl = document.getElementById('chatStatus');
  const theirOnline = (c._other_user_id && onlineStatus[c._other_user_id] === 'online') || c.status === 'online';
  statusEl.textContent = theirOnline ? 'Online · Active now' : 'Last seen recently';
  statusEl.className = 'chat-status' + (theirOnline ? '' : ' away');

  // Listing banner
  const lbImgEl = document.getElementById('lbImg');
  if (c.listing_image_url) {
    lbImgEl.innerHTML = `<img src="${c.listing_image_url}" alt="" style="width:100%;height:100%;object-fit:cover;border-radius:inherit"/>`;
  } else {
    lbImgEl.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>`;
  }
  document.getElementById('lbName').textContent = c.listing;
  document.getElementById('lbPrice').textContent = c.price;

  // Fetch messages & connect WebSocket
  fetchMessages(c.id).then(() => {
    const _tryReadReceipt = (attempt) => {
      if (chatSocket && chatSocket.readyState === WebSocket.OPEN) {
        sendReadReceipts(c.id);
      } else if (attempt < 10) {
        setTimeout(() => _tryReadReceipt(attempt + 1), 150);
      }
    };
    setTimeout(() => _tryReadReceipt(0), 200);
  });
  connectWebSocket(c.id);

  // Restore input state based on blocked status
  const isBlocked = !!c.blocked;
  document.getElementById('msgInput').disabled = isBlocked;
  document.getElementById('msgInput').placeholder = isBlocked ? `You blocked ${c.name}` : 'Type a message…';
  document.getElementById('micBtn').disabled = isBlocked;

  // Quick chips
  renderChips();

  // Show chat view
  document.getElementById('noChatView').style.display = 'none';
  const cv = document.getElementById('chatView');
  cv.classList.remove('dn');
  cv.style.display = 'flex';

  // Mobile: slide right panel in
  if (window.innerWidth < 768) {
    document.getElementById('leftPanel').classList.add('hidden');
    document.getElementById('rightPanel').classList.add('visible');
    const bottomNav = document.querySelector('.bot-nav');
    if (bottomNav) bottomNav.style.display = 'none';
  }

  // Scroll to bottom
  setTimeout(() => { const m = document.getElementById('msgArea'); if (m) m.scrollTop = m.scrollHeight; }, 60);
}

/**
 * Show the left (conversation list) panel on mobile.
 */
function showLeft() {
  document.getElementById('leftPanel').classList.remove('hidden');
  document.getElementById('rightPanel').classList.remove('visible');
  const bottomNav = document.querySelector('.bot-nav');
  if (bottomNav) bottomNav.style.display = '';
  lastConvY = 0;
}

/* ============================================================
   TYPING / RECORDING INDICATORS
   ============================================================ */

function showTyping() {
  removeTyping();
  const area = document.getElementById('msgArea');
  const t = document.createElement('div');
  t.className = 'msg in';
  t.id = 'typingIndicator';
  t.innerHTML = '<div class="typing"><span></span><span></span><span></span></div>';
  area.appendChild(t);
  area.scrollTop = area.scrollHeight;
  typingTimeout = setTimeout(removeTyping, 4000);
}

function showRecording() {
  removeTyping();
  const area = document.getElementById('msgArea');
  const t = document.createElement('div');
  t.className = 'msg in';
  t.id = 'typingIndicator';
  t.innerHTML = '<div class="typing recording-indicator"><svg viewBox="0 0 24 24" style="width:14px;height:14px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round;margin-right:4px"><rect x="9" y="2" width="6" height="11" rx="3"/><path d="M19 10a7 7 0 01-14 0"/><line x1="12" y1="19" x2="12" y2="23"/></svg><span></span><span></span><span></span></div>';
  area.appendChild(t);
  area.scrollTop = area.scrollHeight;
  typingTimeout = setTimeout(removeTyping, 6000);
}

function removeTyping() {
  clearTimeout(typingTimeout);
  const t = document.getElementById('typingIndicator');
  if (t) t.remove();
}

/* ============================================================
   QUICK REPLY CHIPS
   ============================================================ */

function renderChips() {
  const wrap = document.getElementById('quickChips');
  if (!wrap) return;
  wrap.innerHTML = QUICK_REPLIES.map(r =>
    `<div class="chip" onclick="useChip('${escHtml(r)}')">${r}</div>`
  ).join('');
}

function useChip(text) {
  document.getElementById('msgInput').value = text;
  autoResize(document.getElementById('msgInput'));
  toggleSend();
  document.getElementById('msgInput').focus();
}

/* ============================================================
   MEETUP MESSAGES
   ============================================================ */

function sendMeetup(spot, time) {
  if (!activeConv) return;
  if (chatSocket && chatSocket.readyState === WebSocket.OPEN) {
    chatSocket.send(JSON.stringify({
      message: 'I have arranged a meetup.',
      image_url: null,
      voice_url: null,
      meetup_spot: spot,
      meetup_time: time,
    }));
    document.getElementById('schedulerModal').classList.remove('open');
  } else {
    showToast('Not connected');
  }
}

/* ============================================================
   SCROLL TO MESSAGE HELPERS
   ============================================================ */

function scrollToMsg(idx, cid) {
  const el = document.querySelector(`.msg-wrap[data-idx="${idx}"][data-cid="${cid}"]`);
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    el.style.outline = '2px solid rgba(232,201,106,.5)';
    setTimeout(() => el.style.outline = '', 900);
  }
}

function scrollToReply(cid, replyId) {
  const idx = (msgs[cid] || []).findIndex(m => String(m.id) === String(replyId));
  if (idx !== -1) {
    scrollToMsg(idx, cid);
  } else {
    showToast('Original message not found');
  }
}

function scrollToPinned() {
  const bar = document.getElementById('pinnedBar');
  const idx = bar.dataset.idx;
  const cid = activeConv?.id;
  if (idx === undefined || !cid) return;
  const el = document.querySelector(`.msg-wrap[data-idx="${idx}"][data-cid="${cid}"]`);
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    el.style.outline = '2px solid var(--a)';
    setTimeout(() => el.style.outline = '', 1200);
  }
}

function unpinMessage(e) {
  e.stopPropagation();
  const cid = activeConv?.id;
  if (!cid) return;
  msgs[cid].forEach(m => m.pinned = false);
  document.getElementById('pinnedBar').classList.remove('show');
  renderMsgs(cid);
  showToast('Message unpinned');
}

/* ============================================================
   SWIPE TO REPLY
   ============================================================ */

function handleTouchStart(e) {
  if (e.touches.length > 1) return;
  const touch = e.touches[0];
  swipeStartX = touch.clientX;
  swipeStartY = touch.clientY;
  swipeTarget = e.currentTarget;
}

function handleTouchMove(e) {
  if (!swipeTarget) return;
  const touch = e.touches[0];
  const deltaX = touch.clientX - swipeStartX;
  const deltaY = touch.clientY - swipeStartY;
  if (Math.abs(deltaY) > Math.abs(deltaX) * 1.5) return;
  if (Math.abs(deltaX) > 10) e.preventDefault();
}

function handleTouchEnd(e) {
  if (!swipeTarget) return;
  const touch = e.changedTouches[0];
  const deltaX = touch.clientX - swipeStartX;
  const deltaY = touch.clientY - swipeStartY;
  if (Math.abs(deltaX) > swipeThreshold && Math.abs(deltaY) < 80) {
    const isIncoming = swipeTarget.classList.contains('in');
    const isOutgoing = swipeTarget.classList.contains('out');
    if ((isIncoming && deltaX > 0) || (isOutgoing && deltaX < 0)) {
      const idx = parseInt(swipeTarget.dataset.idx);
      const cid = swipeTarget.dataset.cid;
      startReply(idx, cid);
    }
  }
  swipeTarget = null;
}