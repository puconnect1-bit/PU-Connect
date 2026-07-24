/* ============================================================
   WEBSOCKET CONNECTIONS
   ============================================================ */

/**
 * Connect to the presence WebSocket for online/offline status.
 */
function connectPresence() {
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
  presenceSocket = new WebSocket(`${protocol}://${window.location.host}/ws/presence/`);

  presenceSocket.onmessage = function (e) {
    try {
      const data = JSON.parse(e.data);
      if (data.type !== 'presence') return;
      const uid = data.user_id;
      const status = data.status; // 'online' | 'offline'
      onlineStatus[uid] = status;

      // Update conversation list entries
      CONVS.forEach(c => {
        if (c._other_user_id === uid) {
          c.status = status;
        }
      });
      renderConvList(document.getElementById('srchInput').value);

      // Update open chat header if active conv is with this user
      if (activeConv && activeConv._other_user_id === uid) {
        const statusEl = document.getElementById('chatStatus');
        const isOnline = status === 'online';
        statusEl.textContent = isOnline ? 'Online · Active now' : 'Last seen recently';
        statusEl.className = 'chat-status' + (isOnline ? '' : ' away');
      }
    } catch (e) { /* ignore parse errors */ }
  };

  presenceSocket.onclose = function () {
    // Reconnect after 5 s if page is still visible
    setTimeout(() => {
      if (document.visibilityState !== 'hidden') connectPresence();
    }, 5000);
  };

  // Keep-alive ping every 30 s
  setInterval(() => {
    if (presenceSocket && presenceSocket.readyState === WebSocket.OPEN)
      presenceSocket.send('ping');
  }, 30000);
}

/**
 * Send read receipts for unread messages in a conversation.
 * @param {number|string} cid - Conversation ID.
 */
function sendReadReceipts(cid) {
  if (!chatSocket || chatSocket.readyState !== WebSocket.OPEN) return;
  const unread = (msgs[cid] || []).filter(m => m.from === 'in' && m.id && !m.is_read).map(m => m.id);
  if (!unread.length) return;
  chatSocket.send(JSON.stringify({ type: 'read_receipt', message_ids: unread }));
  // Mark locally as read
  unread.forEach(id => {
    const msg = (msgs[cid] || []).find(m => m.id === id);
    if (msg) msg.is_read = true;
  });
}

/**
 * Connect to the chat WebSocket for a specific conversation.
 * @param {number|string} cid - Conversation ID.
 */
function connectWebSocket(cid) {
  if (chatSocket) {
    chatSocket.onclose = null; // Prevent old handler from firing
    chatSocket.close();
  }

  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
  chatSocket = new WebSocket(`${protocol}://${window.location.host}/ws/chat/${cid}/`);

  chatSocket.onmessage = function (e) {
    const data = JSON.parse(e.data);

    // -- Typing indicator --
    if (data.type === 'typing') {
      if (data.sender_id !== currentUserId) {
        if (data.is_typing) showTyping(); else removeTyping();
      }
      return;
    }

    // -- Recording indicator --
    if (data.type === 'recording') {
      if (data.sender_id !== currentUserId) {
        if (data.is_recording) showRecording(); else removeTyping();
      }
      return;
    }

    // -- Read receipt --
    if (data.type === 'read_receipt') {
      const ids = new Set(data.message_ids);
      if (msgs[cid]) {
        msgs[cid].forEach(m => { if (m.id && ids.has(m.id)) m.is_read = true; });
        if (activeConv?.id === cid) renderMsgs(cid);
      }
      return;
    }

    // -- Message deleted (delete for everyone) --
    if (data.type === 'message_deleted') {
      const delId = data.message_id;
      if (msgs[cid]) {
        msgs[cid].forEach(m => { if (m.id == delId) m.is_deleted = true; });
        if (activeConv?.id === cid) renderMsgs(cid);
      }
      return;
    }

    // -- Normal chat message --
    const m = {
      id: data.msg_id || null,
      from: data.sender_id === currentUserId ? 'out' : 'in',
      text: data.message,
      image_url: data.image_url,
      voice_url: data.voice_url,
      voice_duration: data.voice_duration || 0,
      meetup_spot: data.meetup_spot,
      meetup_time: data.meetup_time,
      time: data.timestamp,
      is_read: data.is_read || false,
      is_deleted: data.is_deleted || false,
      reply_to: data.reply_to_id || null,
      reply_to_name: data.reply_to_name || null,
      reply_to_text: data.reply_to_text || null,
    };

    // Store voice note in vnAudioMap for playback
    if (m.voice_url && m.id) {
      const stableId = 'srv-' + cid + '-' + m.id;
      vnAudioMap[stableId] = {
        url: m.voice_url,
        duration: m.voice_duration || 0,
        waveform: generateFlatWaveform(28),
      };
    }

    if (!msgs[cid]) msgs[cid] = [];

    // Resolve optimistic pending message
    if (m.from === 'out' && m.text) {
      const pendingIdx = msgs[cid].findIndex(msg => msg.pending && msg.text === m.text);
      if (pendingIdx !== -1) {
        msgs[cid][pendingIdx] = m;
        if (activeConv?.id === cid) renderMsgs(cid);
        fetchConversations();
        return;
      }
    }

    // Incoming message
    removeTyping();
    msgs[cid].push(m);
    if (activeConv?.id === cid) {
      renderMsgs(cid);
      if (m.from === 'in' && m.id) {
        sendReadReceipts(cid);
      }
    }
    fetchConversations();
  };

  chatSocket.onerror = function (e) {
    console.warn('Chat socket error', e);
  };

  chatSocket.onclose = function (e) {
    console.warn('Chat socket closed — reconnecting in 3s...');
    setTimeout(() => { if (activeConv) connectWebSocket(activeConv.id); }, 3000);
  };
}

/**
 * Send a typing signal via WebSocket.
 * @param {boolean} isTyping
 */
function sendTypingSignal(isTyping) {
  if (!chatSocket || chatSocket.readyState !== WebSocket.OPEN) return;
  chatSocket.send(JSON.stringify({ type: 'typing', is_typing: isTyping }));
}