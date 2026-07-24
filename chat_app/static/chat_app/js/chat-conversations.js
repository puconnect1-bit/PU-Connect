/* ============================================================
   CONVERSATION LIST MANAGEMENT
   ============================================================ */

/**
 * Fetch all conversations from the API.
 */
async function fetchConversations() {
  try {
    const res = await fetch('/chat/api/conversations/');
    CONVS = await res.json();
    // Seed real-time presence from our local map
    CONVS.forEach(c => {
      c._other_user_id = c.other_user_id;
      if (c._other_user_id && onlineStatus[c._other_user_id]) {
        c.status = onlineStatus[c._other_user_id];
      }
    });
    renderConvList();
  } catch (e) {
    console.error('Failed to fetch convs', e);
  }
}

/**
 * Render the conversation list with optional search filter and tab.
 * @param {string} [filter=''] - Search filter text.
 * @param {string} [tab=activeTab] - Active tab filter.
 */
function renderConvList(filter = '', tab = activeTab) {
  const list = document.getElementById('convList');
  if (!list) return;

  let data = CONVS.filter(c => {
    const matchSearch = !filter ||
      c.name.toLowerCase().includes(filter.toLowerCase()) ||
      c.listing.toLowerCase().includes(filter.toLowerCase());
    const matchTab = tab === 'all' ||
      (tab === 'unread' && c.badge > 0) ||
      c.type === tab;
    return matchSearch && matchTab;
  });

  if (!data.length) {
    list.innerHTML = `<div class="empty-convs"><div class="empty-ico"></div><div class="empty-t">No conversations found</div></div>`;
    return;
  }

  list.innerHTML = data.map(c => {
    const lastMsg = msgs[c.id]?.[msgs[c.id].length - 1];
    const preview = lastMsg
      ? (lastMsg.text ||
          (lastMsg.image_url ? '📷 Photo' : lastMsg.voice_url ? '🎤 Voice note' : lastMsg.offer ? `Offer: ${lastMsg.offer.amount}` : lastMsg.meetup_spot ? `📍 ${lastMsg.meetup_spot}` : '')) || ''
      : '';
    const isUnread = c.badge > 0;
    const avatarHTML = c.avatar_url
      ? `<img src="${c.avatar_url}" alt="" style="width:100%;height:100%;object-fit:cover;border-radius:50%"/>`
      : AV_SVG;

    return `<div class="conv${activeConv?.id === c.id ? ' active' : ''}" onclick="openConvById('${c.id}')" id="cv${c.id}">
      <div class="conv-av">
        ${avatarHTML}
        ${c.status === 'online' ? '<div class="online-dot"></div>' : ''}
      </div>
      <div class="conv-body">
        <div class="conv-top">
          <div class="conv-name">${escHtml(c.name)}</div>
          <div class="conv-time">${c.time}</div>
        </div>
        <div class="conv-bottom">
          <div class="conv-preview${isUnread ? ' unread' : ''}">${escHtml(preview)}</div>
          ${c.badge ? `<div class="conv-badge">${c.badge}</div>` : ''}
        </div>
        <div class="conv-listing-tag">${c.listingEmoji} ${escHtml(c.listing)}</div>
      </div>
    </div>`;
  }).join('');
}

/**
 * Open a conversation by its ID.
 * @param {number|string} id - Conversation ID.
 */
function openConvById(id) {
  const c = CONVS.find(x => String(x.id) === String(id));
  if (c) openConv(c);
}

/**
 * Filter conversations by search input.
 * @param {string} v - Search value.
 */
function filterConvs(v) {
  renderConvList(v, activeTab);
}

/**
 * Switch the active tab and re-render the conversation list.
 * @param {HTMLElement} el - The clicked tab element.
 * @param {string} tab - Tab name: 'all' | 'buying' | 'selling' | 'unread'.
 */
function switchTab(el, tab) {
  activeTab = tab;
  document.querySelectorAll('.ltab').forEach(t => t.classList.remove('on'));
  el.classList.add('on');
  renderConvList(document.getElementById('srchInput').value, tab);
}