/* ============================================================
   VOICE NOTE RECORDING & PLAYBACK
   ============================================================ */

/* ---- RECORDING ---- */

/**
 * Toggle voice recording on/off.
 */
async function toggleRecording() {
  if (mediaRecorder && mediaRecorder.state === 'recording') {
    stopAndSend();
  } else {
    await startRecording();
  }
}

/**
 * Start recording a voice note.
 */
async function startRecording() {
  try {
    recStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
  } catch (e) {
    showToast('Microphone access denied. Please allow mic access in your browser settings.');
    return;
  }

  // AudioContext for live waveform
  audioCtxRec = new (window.AudioContext || window.webkitAudioContext)();
  if (audioCtxRec.state === 'suspended') await audioCtxRec.resume();

  const source = audioCtxRec.createMediaStreamSource(recStream);
  analyserNode = audioCtxRec.createAnalyser();
  analyserNode.fftSize = 512;
  analyserNode.smoothingTimeConstant = 0.5;
  source.connect(analyserNode);

  recChunks = [];
  waveformAmps = [];

  // Notify the other user we're recording
  if (chatSocket && chatSocket.readyState === WebSocket.OPEN)
    chatSocket.send(JSON.stringify({ type: 'recording', is_recording: true }));

  const mime = getSupportedMime();
  mediaRecorder = new MediaRecorder(recStream, { mimeType: mime });
  mediaRecorder.ondataavailable = e => { if (e.data && e.data.size > 0) recChunks.push(e.data); };
  mediaRecorder.start(100);

  // Show recording bar UI
  document.getElementById('inputRow').style.display = 'none';
  document.getElementById('recBar').classList.add('active');

  // Build live waveform slots
  const wf = document.getElementById('recWaveform');
  wf.innerHTML = '';
  for (let i = 0; i < 28; i++) {
    const b = document.createElement('div');
    b.className = 'rec-bar-el';
    b.style.height = '3px';
    wf.appendChild(b);
  }

  // Start timer
  recSeconds = 0;
  document.getElementById('recTimer').textContent = '0:00';
  recTimerInterval = setInterval(() => {
    recSeconds++;
    document.getElementById('recTimer').textContent = fmtDur(recSeconds);
    if (recSeconds >= 120) stopAndSend();
  }, 1000);

  animateRecWaveform();
}

/**
 * Animate the live recording waveform.
 */
function animateRecWaveform() {
  if (!analyserNode) return;
  const bars = document.getElementById('recWaveform').querySelectorAll('.rec-bar-el');
  const buf = new Uint8Array(analyserNode.frequencyBinCount);

  function draw() {
    if (!mediaRecorder || mediaRecorder.state !== 'recording') return;
    analyserNode.getByteTimeDomainData(buf);
    let sum = 0;
    for (let i = 0; i < buf.length; i++) {
      const v = (buf[i] - 128) / 128;
      sum += v * v;
    }
    const rms = Math.sqrt(sum / buf.length);
    const h = Math.max(3, Math.min(22, Math.round(rms * 140)));
    waveformAmps.push(h);
    const arr = Array.from(bars);
    for (let i = 0; i < arr.length - 1; i++) arr[i].style.height = arr[i + 1].style.height;
    arr[arr.length - 1].style.height = h + 'px';
    animFrameRec = requestAnimationFrame(draw);
  }
  animFrameRec = requestAnimationFrame(draw);
}

/**
 * Stop recording and send the voice note.
 */
function stopAndSend() {
  if (!mediaRecorder || mediaRecorder.state === 'inactive') return;

  const capturedSeconds = recSeconds;
  const capturedAmps = [...waveformAmps];
  const capturedMime = getSupportedMime();

  mediaRecorder.onstop = () => {
    if (!recChunks.length) { showToast('Recording too short — try again'); return; }

    const blob = new Blob(recChunks, { type: capturedMime });
    const url = URL.createObjectURL(blob);

    // Downsample amplitude array to 24 bars
    const TARGET = 24;
    const amps = capturedAmps.length >= TARGET ? capturedAmps : [...capturedAmps, ...Array(TARGET).fill(3)];
    const step = Math.max(1, amps.length / TARGET);
    const sampled = Array.from({ length: TARGET }, (_, i) =>
      amps[Math.min(Math.floor(i * step), amps.length - 1)] || 3
    );
    const max = Math.max(...sampled, 1);
    const normalised = sampled.map(v => Math.max(3, Math.round((v / max) * 20)));

    const duration = Math.max(1, capturedSeconds);
    sendVoiceNote(url, duration, normalised);
  };

  // Notify the other user we stopped recording
  if (chatSocket && chatSocket.readyState === WebSocket.OPEN)
    chatSocket.send(JSON.stringify({ type: 'recording', is_recording: false }));

  mediaRecorder.stop();
  cleanupRecording();
}

/**
 * Cancel the current recording.
 */
function cancelRecording() {
  if (chatSocket && chatSocket.readyState === WebSocket.OPEN)
    chatSocket.send(JSON.stringify({ type: 'recording', is_recording: false }));
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.ondataavailable = null;
    mediaRecorder.onstop = null;
    mediaRecorder.stop();
  }
  cleanupRecording();
}

/**
 * Cleanup recording UI and hardware resources.
 */
function cleanupRecording() {
  clearInterval(recTimerInterval);
  if (animFrameRec) { cancelAnimationFrame(animFrameRec); animFrameRec = null; }
  if (recStream) { recStream.getTracks().forEach(t => t.stop()); recStream = null; }
  if (audioCtxRec) { audioCtxRec.close().catch(() => {}); audioCtxRec = null; }
  analyserNode = null;
  document.getElementById('recBar').classList.remove('active');
  document.getElementById('inputRow').style.display = 'flex';
}

/**
 * Send a voice note (optimistic local + upload to R2).
 * @param {string} url - Blob URL of the recording.
 * @param {number} duration - Duration in seconds.
 * @param {number[]} waveform - Waveform amplitude array.
 */
function sendVoiceNote(url, duration, waveform) {
  if (!activeConv) return;

  // Optimistic local bubble
  const stableId = 'vn' + (++vnCounter);
  vnAudioMap[stableId] = { url, duration, waveform };
  const now = new Date();
  const time = now.toLocaleTimeString('en-GH', { hour: 'numeric', minute: '2-digit', hour12: true });
  msgs[activeConv.id].push({ from: 'out', voice: { stableId, url, duration, waveform }, time });
  const ci = CONVS.find(x => x.id === activeConv.id);
  if (ci) ci.time = 'Just now';
  renderMsgs(activeConv.id);
  renderConvList(document.getElementById('srchInput').value);

  // Upload to R2 and send via WebSocket
  if (chatSocket && chatSocket.readyState === WebSocket.OPEN) {
    fetch(url)
      .then(res => res.blob())
      .then(blob => uploadToR2(blob, 'voice'))
      .then(publicUrl => {
        chatSocket.send(JSON.stringify({
          message: null,
          image_url: null,
          voice_url: publicUrl,
          voice_duration: duration,
        }));
      })
      .catch(err => {
        console.error('Voice note upload failed:', err);
        showToast('Voice note upload failed — try again');
      });
  } else {
    showToast('Not connected — voice note saved locally');
  }
}

/* ---- PLAYBACK ---- */

/**
 * Play or pause a voice note.
 * @param {string} id - The stable ID of the voice note.
 */
function playVoice(id) {
  const data = vnAudioMap[id];
  if (!data) { showToast('Voice note not ready'); return; }

  // Same note playing → pause
  if (currentVnId === id && currentAudio && !currentAudio.paused) {
    currentAudio.pause();
    return;
  }

  // Same note paused → resume
  if (currentVnId === id && currentAudio && currentAudio.paused && currentAudio.currentTime > 0) {
    currentAudio.playbackRate = data._speed || 1;
    currentAudio.play().catch(() => showToast('Playback failed'));
    setPauseIcon(id);
    animateVnProgress(id);
    return;
  }

  // Different note playing → reset
  if (currentAudio && !currentAudio.paused) {
    currentAudio.pause();
    if (currentVnId && currentVnId !== id) resetVnUI(currentVnId);
  }

  // Fresh play
  const audio = new Audio(data.url);
  audio.playbackRate = data._speed || 1;
  currentAudio = audio;
  currentVnId = id;

  // Restore position if scrubbed while paused
  if (data._resumeAt) {
    audio.addEventListener('loadedmetadata', () => { audio.currentTime = data._resumeAt; }, { once: true });
  }

  audio.addEventListener('canplay', () => {
    audio.play().catch(() => {
      showToast('Playback failed — try again');
      setPlayIcon(id);
      currentAudio = null;
      currentVnId = null;
    });
  }, { once: true });

  audio.addEventListener('play', () => {
    setPauseIcon(id);
    document.getElementById('pwrap-' + id)?.classList.add('playing');
    animateVnProgress(id);
  }, { once: true });

  audio.onpause = () => {
    setPlayIcon(id);
    document.getElementById('pwrap-' + id)?.classList.remove('playing');
    if (data._raf) { cancelAnimationFrame(data._raf); data._raf = null; }
    if (!audio.ended) data._resumeAt = audio.currentTime;
  };

  audio.onended = () => {
    setPlayIcon(id);
    document.getElementById('pwrap-' + id)?.classList.remove('playing');
    if (data._raf) { cancelAnimationFrame(data._raf); data._raf = null; }
    data._resumeAt = 0;
    const prog = document.getElementById('prog-' + id);
    const durEl = document.getElementById('dur-' + id);
    if (prog) prog.style.width = '0%';
    if (durEl) durEl.textContent = fmtDur(data.duration);
    resetVnBars(id);
    currentVnId = null;
    currentAudio = null;
  };

  audio.onerror = (e) => {
    console.error('Voice note playback error:', e);
    showToast('Could not load voice note');
    setPlayIcon(id);
    currentAudio = null;
    currentVnId = null;
  };

  audio.play().catch(err => {
    console.error('Playback failed:', err);
    showToast('Playback failed — try again');
    setPlayIcon(id);
    currentAudio = null;
    currentVnId = null;
  });
}

/**
 * Animate the voice note progress bar during playback.
 * @param {string} id - Stable voice note ID.
 */
function animateVnProgress(id) {
  const audio = currentAudio;
  const data = vnAudioMap[id];
  if (!audio || !data) return;

  function frame() {
    if (!audio || audio.paused || audio.ended) return;
    const dur = audio.duration || data.duration || 1;
    const pct = (audio.currentTime / dur) * 100;

    const prog = document.getElementById('prog-' + id);
    const thumb = document.getElementById('thumb-' + id);
    const durEl = document.getElementById('dur-' + id);
    const barsEl = document.getElementById('bars-' + id);

    if (prog) prog.style.width = pct + '%';
    if (thumb) thumb.style.left = pct + '%';
    if (durEl) durEl.textContent = '-' + fmtDur(Math.max(0, dur - audio.currentTime));

    if (barsEl) {
      const bars = barsEl.querySelectorAll('.vn-bar');
      const playedCount = Math.round((pct / 100) * bars.length);
      bars.forEach((b, i) => b.classList.toggle('played', i < playedCount));
    }
    data._raf = requestAnimationFrame(frame);
  }
  data._raf = requestAnimationFrame(frame);
}

/**
 * Seek to a position in the voice note.
 * @param {Event} e - Click event.
 * @param {string} id - Stable voice note ID.
 */
function seekVoice(e, id) {
  const data = vnAudioMap[id];
  if (!data) return;
  const rect = e.currentTarget.getBoundingClientRect();
  const pct = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
  if (currentAudio && currentVnId === id && currentAudio.duration) {
    currentAudio.currentTime = pct * currentAudio.duration;
  } else {
    const dur = data.duration || 0;
    data._resumeAt = pct * dur;
    playVoice(id);
  }
}

/**
 * Show seek tooltip on hover.
 */
function vnSeekHover(e, id) {
  const data = vnAudioMap[id];
  if (!data) return;
  const tip = document.getElementById('tip-' + id);
  if (!tip) return;
  const rect = e.currentTarget.getBoundingClientRect();
  const pct = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
  const dur = data.duration || (currentAudio && currentVnId === id ? currentAudio.duration : 0) || 0;
  tip.textContent = fmtDur(pct * dur);
  tip.style.left = Math.round(pct * rect.width) + 'px';
  tip.style.display = 'block';
}

function vnSeekLeave(id) {
  const tip = document.getElementById('tip-' + id);
  if (tip) tip.style.display = 'none';
}

/* ---- SPEED CONTROL ---- */

function cycleSpeed(id) {
  const data = vnAudioMap[id];
  if (!data) return;
  const speeds = VN_SPEEDS;
  const cur = data._speed || 1;
  const next = speeds[(speeds.indexOf(cur) + 1) % speeds.length];
  data._speed = next;
  const btn = document.getElementById('spd-' + id);
  if (btn) {
    btn.textContent = next + '×';
    btn.classList.toggle('active', next !== 1);
  }
  if (currentAudio && currentVnId === id) currentAudio.playbackRate = next;
}

/* ---- UI HELPERS ---- */

function setPlayIcon(id) {
  const btn = document.getElementById('play-' + id);
  if (!btn) return;
  btn.classList.remove('playing');
  btn.innerHTML = '<svg viewBox="0 0 24 24"><polygon points="5 3 19 12 5 21 5 3"/></svg>';
}

function setPauseIcon(id) {
  const btn = document.getElementById('play-' + id);
  if (!btn) return;
  btn.classList.add('playing');
  btn.innerHTML = '<svg viewBox="0 0 24 24"><line x1="6" y1="4" x2="6" y2="20"/><line x1="18" y1="4" x2="18" y2="20"/></svg>';
}

function resetVnUI(id) {
  setPlayIcon(id);
  const prog = document.getElementById('prog-' + id);
  const dur = document.getElementById('dur-' + id);
  const data = vnAudioMap[id];
  if (prog) prog.style.width = '0%';
  if (dur && data) dur.textContent = fmtDur(data.duration);
  resetVnBars(id);
  document.getElementById('pwrap-' + id)?.classList.remove('playing');
}

function resetVnBars(id) {
  const barsEl = document.getElementById('bars-' + id);
  if (barsEl) barsEl.querySelectorAll('.vn-bar').forEach(b => b.classList.remove('played'));
}