/* ============================================================
   MODAL MANAGEMENT
   ============================================================ */

/* ---- NEW CHAT MODAL ---- */

function openNewChat() {
  document.getElementById('ncSearchInput').value = '';
  document.getElementById('ncResults').innerHTML = '';
  document.getElementById('ncSuggested').parentElement.style.display = 'block';
  document.getElementById('ncSuggested').innerHTML = '';
  document.getElementById('newChatModal').classList.add('open');
  setTimeout(() => document.getElementById('ncSearchInput').focus(), 300);
}

function closeNewChat(e) {
  if (!e || e.target === document.getElementById('newChatModal'))
    document.getElementById('newChatModal').classList.remove('open');
}

function searchUsers(q) {
  const res = document.getElementById('ncResults');
  const sug = document.getElementById('ncSuggested');
  clearTimeout(_searchTimer);
  if (!q.trim()) {
    res.innerHTML = '';
    sug.parentElement.style.display = 'block';
    return;
  }
  sug.parentElement.style.display = 'none';
  res.innerHTML = '<div style="text-align:center;padding:1rem;color:var(--m);font-size:.84rem">Searching…</div>';
  _searchTimer = setTimeout(async () => {
    try {
      const r = await fetch(`/chat/api/search-users/?q=${encodeURIComponent(q.replace('@', ''))}`);
      const users = await r.json();
      if (!users.length) {
        res.innerHTML = `<div style="text-align:center;padding:1.5rem;color:var(--m);font-size:.85rem">No users found for "${escHtml(q)}"</div>`;
        return;
      }
      res.innerHTML = users.map(u => userRowHTML(u)).join('');
    } catch (e) {
      res.innerHTML = '<div style="text-align:center;padding:1rem;color:var(--red);font-size:.84rem">Search failed — try again</div>';
    }
  }, 350);
}

function userRowHTML(u) {
  const avatarHTML = u.avatar_url
    ? `<img src="${u.avatar_url}" alt="" style="width:100%;height:100%;object-fit:cover;border-radius:50%"/>`
    : AV_SVG;
  const convId = u.conv_id || u.convId || null;
  const vbadge = u.is_verified
    ? '<span class="pu-verified pu-verified-sm" title="Verified Student"><svg viewBox="0 0 24 24"><polyline points="4 12 9 17 20 6"/></svg></span>'
    : '';
  return `<div class="nc-user" onclick='startChat(${JSON.stringify({ id: u.id, name: u.name, username: u.username, avatar_url: u.avatar_url || '', convId: convId })})'>
    <div class="nc-av">${avatarHTML}</div>
    <div class="nc-info">
      <div class="nc-name">${escHtml(u.name)}${vbadge}</div>
      <div class="nc-uname">@${escHtml(u.username)}</div>
    </div>
    ${convId ? '<span style="font-size:.7rem;color:var(--a);background:rgba(232,201,106,.12);padding:.15rem .5rem;border-radius:5px">Chat</span>' : ''}
  </div>`;
}

async function startChat(user) {
  document.getElementById('newChatModal').classList.remove('open');
  // If existing conv is already loaded, open it directly
  if (user.convId) {
    const existing = CONVS.find(x => String(x.id) === String(user.convId));
    if (existing) { openConv(existing); return; }
  }
  // Create or retrieve a direct conversation via backend
  try {
    const csrf = document.cookie.split('; ').find(r => r.startsWith('csrftoken='))?.split('=')[1] || '';
    const res = await fetch('/chat/api/start-direct/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
      body: JSON.stringify({ username: user.username }),
    });
    if (!res.ok) {
      showToast('Could not open conversation — try again');
      return;
    }
    const d = await res.json();
    if (d.status === 'success') {
      await fetchConversations();
      const conv = CONVS.find(c => String(c.id) === String(d.conv_id));
      if (conv) { openConv(conv); return; }
      // Fallback: open with a minimal stub
      const stub = {
        id: d.conv_id,
        name: user.name || user.username,
        username: user.username,
        avatar_url: user.avatar_url || '',
        listing: 'General',
        listingEmoji: '💬',
        price: '',
        time: 'Now',
        badge: 0,
        type: 'direct',
        status: 'away',
        _other_user_id: user.id,
        blocked: false,
      };
      CONVS.unshift(stub);
      openConv(stub);
      return;
    }
    showToast(d.message || 'Could not open conversation — try again');
  } catch (e) {
    console.error('startChat error', e);
    showToast('Could not open conversation — try again');
  }
}

/* ---- SCHEDULER MODAL ---- */

function openScheduler() {
  closeMoreMenu();
  const d = new Date();
  d.setDate(d.getDate() + 1);
  document.getElementById('schedDate').value = d.toISOString().split('T')[0];
  document.getElementById('schedTime').value = '09:00';
  document.getElementById('schedSpot').value = '';
  document.getElementById('schedNote').value = '';
  document.getElementById('schedulerModal').classList.add('open');
}

function closeScheduler(e) {
  if (!e || e.target === document.getElementById('schedulerModal'))
    document.getElementById('schedulerModal').classList.remove('open');
}

function confirmSchedule() {
  const date = document.getElementById('schedDate').value;
  const time = document.getElementById('schedTime').value;
  const spot = document.getElementById('schedSpot').value.trim();
  const note = document.getElementById('schedNote').value.trim();
  if (!date || !time || !spot) { showToast('Please fill in date, time and meetup spot'); return; }

  const d = new Date(date + 'T' + time);
  const opts = { weekday: 'short', month: 'short', day: 'numeric' };
  const dateStr = d.toLocaleDateString('en-GH', opts) + ', ' + d.toLocaleTimeString('en-GH', { hour: 'numeric', minute: '2-digit', hour12: true });

  const fullSpot = note ? `${spot} (${note})` : spot;
  sendMeetup(fullSpot, dateStr);
}

/* ---- LISTING MODAL ---- */

function openListing() {
  closeMoreMenu();
  if (!activeConv) return;
  const det = LISTING_DETAILS[activeConv.id] || { desc: 'No description available.', badge: 'Available' };
  const lmImgEl = document.getElementById('lmImg');
  if (activeConv.listing_image_url) {
    lmImgEl.innerHTML = `<img src="${activeConv.listing_image_url}" alt="" style="width:100%;height:100%;object-fit:cover;border-radius:inherit"/>`;
  } else {
    lmImgEl.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>`;
  }
  document.getElementById('lmName').textContent = activeConv.listing;
  document.getElementById('lmPrice').textContent = activeConv.price || '—';
  document.getElementById('lmSeller').textContent = `Listed by ${activeConv.role === 'seller' ? activeConv.name : 'You'}`;
  document.getElementById('lmBadge').textContent = det.badge;
  document.getElementById('lmDesc').textContent = det.desc;
  document.getElementById('listingModal').classList.add('open');
}

function closeListingModal(e) {
  if (!e || e.target === document.getElementById('listingModal')) {
    document.getElementById('listingModal').classList.remove('open');
    document.getElementById('sendPhotosBtn').style.display = 'flex';
  }
}

/* ---- USER PROFILE MODAL ---- */

function viewProfile() {
  closeMoreMenu();
  if (!activeConv) return;
  const c = activeConv;
  const d = UP_DATA[c.id] || {
    username: c.name.toLowerCase().replace(' ', '_'),
    bio: 'Campus marketplace member.',
    faculty: '—',
    location: '—',
    listings: 0,
    sold: 0,
    rating: '—',
    badges: [{ cls: 'gold', t: 'Verified Student' }],
    items: [],
  };

  // Avatar
  const avEl = document.getElementById('upAvatar');
  avEl.className = 'up-avatar ' + c.avCls;
  document.getElementById('upAvatarInitials').innerHTML = AV_SVG;
  document.getElementById('upAvatarInitials').style.display = '';
  document.getElementById('upAvatarImg').style.display = 'none';

  // Online dot
  const myOnline = localStorage.getItem('pu-online-status') !== 'offline';
  const theirOnline = c.status === 'online' && myOnline;
  const dot = document.getElementById('upOnlineDot');
  dot.className = 'up-online-dot' + (theirOnline ? '' : ' offline');

  // Text fields
  document.getElementById('upName').textContent = c.name;
  document.getElementById('upUsername').textContent = '@' + d.username;
  document.getElementById('upBio').textContent = d.bio;

  // Tags
  document.getElementById('upTags').innerHTML =
    `<span class="up-tag">${d.location}</span>` +
    `<span class="up-tag">${d.faculty}</span>` +
    (theirOnline
      ? '<span class="up-tag" style="color:#22c55e">Online now</span>'
      : '<span class="up-tag">Last seen recently</span>');

  // Stats
  document.getElementById('upListings').textContent = d.listings;
  document.getElementById('upSold').textContent = d.sold;
  document.getElementById('upRating').textContent = d.rating;

  // Badges
  document.getElementById('upBadges').innerHTML = d.badges.map(b =>
    `<span class="up-badge ${b.cls}">${b.t}</span>`
  ).join('');

  // Mini listing cards
  document.getElementById('upListingsScroll').innerHTML = d.items.map(item =>
    `<div class="up-lcard">
      <div class="up-lcard-img">${item.e}</div>
      <div class="up-lcard-body">
        <div class="up-lcard-name">${item.n}</div>
        <div class="up-lcard-price">${item.p}</div>
      </div>
    </div>`
  ).join('');

  document.getElementById('userProfileModal').classList.add('open');
}

function closeUserProfile(e) {
  if (!e || e.target === document.getElementById('userProfileModal'))
    document.getElementById('userProfileModal').classList.remove('open');
}

/* ---- REPORT MODAL ---- */

function reportUser() {
  closeMoreMenu();
  if (!activeConv) return;
  document.querySelectorAll('.report-pill').forEach(p => p.classList.remove('selected'));
  document.getElementById('reportDetails').value = '';
  document.getElementById('reportCharCount').textContent = '0 / 500';
  document.getElementById('reasonErr').classList.remove('show');
  document.getElementById('reportModalSub').textContent = `Reporting ${activeConv.name}`;
  document.getElementById('reportSubmitBtn').textContent = 'Submit Report';
  document.getElementById('reportSubmitBtn').disabled = false;
  document.getElementById('reportModal').classList.add('open');
}

function closeReportModal(e) {
  if (!e || e.target === document.getElementById('reportModal'))
    document.getElementById('reportModal').classList.remove('open');
}

function selectReason(el, _) {
  document.querySelectorAll('.report-pill').forEach(p => p.classList.remove('selected'));
  el.classList.add('selected');
  document.getElementById('reasonErr').classList.remove('show');
}

function updateReportCount(el) {
  const n = el.value.length;
  const counter = document.getElementById('reportCharCount');
  counter.textContent = `${n} / 500`;
  counter.style.color = n > 450 ? 'var(--red)' : 'var(--m)';
}

function submitReport() {
  const selected = document.querySelector('.report-pill.selected');
  if (!selected) {
    document.getElementById('reasonErr').classList.add('show');
    return;
  }
  const btn = document.getElementById('reportSubmitBtn');
  btn.textContent = 'Submitting…';
  btn.disabled = true;
  // Simulate sending
  setTimeout(() => {
    document.getElementById('reportModal').classList.remove('open');
    showToast('Report sent — our safety team will review within 2 hours');
  }, 900);
}

/* ---- PHOTO MODAL ---- */

function triggerPhotoUpload() {
  document.getElementById('photoFileInput').click();
}

function handlePhotoUpload(files) {
  if (!files.length) return;
  pendingPhotos = [];
  const validFiles = Array.from(files).filter(f => f.type.startsWith('image/')).slice(0, 6);
  if (!validFiles.length) return;
  const grid = document.getElementById('photoPreviewGrid');
  grid.innerHTML = '<div style="padding:1.5rem;text-align:center;color:var(--m);font-size:.84rem">Uploading photos...</div>';
  document.getElementById('photoPreviewModal').classList.add('open');
  document.getElementById('photoFileInput').value = '';
  Promise.all(validFiles.map(f =>
    uploadToR2(f, 'image').catch(err => { console.error(err); return null; })
  )).then(urls => {
    pendingPhotos = urls.filter(Boolean);
    if (!pendingPhotos.length) {
      document.getElementById('photoPreviewModal').classList.remove('open');
      return;
    }
    grid.innerHTML = pendingPhotos.map(src => `<img src="${src}" alt="preview"/>`).join('');
    document.getElementById('photoCount').textContent = `${pendingPhotos.length} photo${pendingPhotos.length > 1 ? 's' : ''}`;
  }).catch(() => {
    document.getElementById('photoPreviewModal').classList.remove('open');
  });
}

function sendPhotos() {
  if (!pendingPhotos.length || !activeConv) return;
  const now = new Date();
  const time = now.toLocaleTimeString('en-GH', { hour: 'numeric', minute: '2-digit', hour12: true });
  msgs[activeConv.id].push({ from: 'out', images: [...pendingPhotos], time });
  const ci = CONVS.find(x => x.id === activeConv.id);
  if (ci) ci.time = 'Just now';
  pendingPhotos = [];
  document.getElementById('photoPreviewModal').classList.remove('open');
  renderMsgs(activeConv.id);
  renderConvList(document.getElementById('srchInput').value);
}

function closePhotoPreview(e) {
  if (!e || e.target === document.getElementById('photoPreviewModal')) {
    document.getElementById('photoPreviewModal').classList.remove('open');
    pendingPhotos = [];
  }
}

function previewFullImg(src) {
  const grid = document.getElementById('photoPreviewGrid');
  grid.innerHTML = `<img src="${src}" alt="full" style="grid-column:1/-1;aspect-ratio:auto;border-radius:12px"/>`;
  document.getElementById('photoCount').textContent = '';
  document.getElementById('sendPhotosBtn').style.display = 'none';
  document.getElementById('photoPreviewModal').classList.add('open');
}

/* ---- MORE OPTIONS MENU ---- */

function toggleMoreMenu() {
  const menu = document.getElementById('moreMenu');
  const ov = document.getElementById('moreOverlay');
  const isOpen = menu.classList.contains('open');
  if (isOpen) { closeMoreMenu(); } else {
    if (activeConv) {
      const blocked = !!activeConv.blocked;
      document.getElementById('blockMenuLabel').textContent = blocked ? 'Unblock User' : 'Block User';
      document.getElementById('blockMenuItem').style.color = blocked ? 'var(--a2)' : 'var(--red)';
    }
    menu.classList.add('open');
    ov.classList.add('open');
  }
}

function closeMoreMenu() {
  document.getElementById('moreMenu').classList.remove('open');
  document.getElementById('moreOverlay').classList.remove('open');
}

/* ---- BLOCK / CLEAR CHAT ---- */

function clearChat() {
  closeMoreMenu();
  if (!activeConv) return;
  puConfirm(
    `Clear all messages with <strong>${activeConv.name}</strong>? This cannot be undone.`,
    () => { msgs[activeConv.id] = []; renderMsgs(activeConv.id); showToast('Chat cleared'); },
    { icon: '🗑️', okLabel: 'Clear', danger: true }
  );
}

function blockUser() {
  closeMoreMenu();
  if (!activeConv) return;
  const blocked = !!activeConv.blocked;

  if (blocked) {
    // UNBLOCK
    puConfirm(
      `Unblock <strong>${activeConv.name}</strong>? They'll be able to message you again.`,
      () => {
        activeConv.blocked = false;
        const cid = activeConv.id;
        msgs[cid] = msgs[cid].filter(m => m._blockedBanner !== cid);
        renderMsgs(cid);
        document.getElementById('msgInput').disabled = false;
        document.getElementById('msgInput').placeholder = 'Type a message…';
        document.getElementById('micBtn').disabled = false;
        showToast(`${activeConv.name} has been unblocked`);
      },
      { icon: '🔓', okLabel: 'Unblock' }
    );
  } else {
    // BLOCK
    puConfirm(
      `Block <strong>${activeConv.name}</strong>? They won't be able to message you.`,
      () => {
        activeConv.blocked = true;
        const cid = activeConv.id;
        const now = new Date();
        const time = now.toLocaleTimeString('en-GH', { hour: 'numeric', minute: '2-digit', hour12: true });
        msgs[cid].push({ from: 'system', text: `You blocked ${activeConv.name}. They can no longer send you messages.`, time, _blockedBanner: cid });
        renderMsgs(cid);
        document.getElementById('msgInput').disabled = true;
        document.getElementById('msgInput').placeholder = `You blocked ${activeConv.name}`;
        document.getElementById('micBtn').disabled = true;
        showToast(`${activeConv.name} has been blocked`);
      },
      { icon: '🚫', okLabel: 'Block', danger: true }
    );
  }
}

/* ---- OFFER ACTIONS ---- */

function acceptOffer(btn, cid) {
  const card = btn.closest('.offer-card');
  card.querySelector('.offer-btns').innerHTML = '<div class="offer-accepted">Offer accepted</div>';
  const area = document.getElementById('msgArea');
  const s = document.createElement('div');
  s.className = 'sys-msg';
  s.textContent = 'You accepted the offer. Arrange a meetup to complete the trade.';
  area.appendChild(s);
  area.scrollTop = area.scrollHeight;
  showToast('Offer accepted! Arrange a meetup to complete the trade.');
}

function declineOffer(btn) {
  const card = btn.closest('.offer-card');
  card.querySelector('.offer-btns').remove();
  const d = document.createElement('div');
  d.style.cssText = 'font-size:.74rem;color:var(--red);margin-top:.4rem';
  d.textContent = '❌ Offer declined';
  card.appendChild(d);
  showToast('Offer declined.');
}