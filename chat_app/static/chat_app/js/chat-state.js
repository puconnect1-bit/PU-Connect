/* ============================================================
   CHAT APPLICATION STATE
   ============================================================ */

/** Default avatar SVG */
const AV_SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" style="width:100%;height:100%;border-radius:50%;display:block"><circle cx="20" cy="20" r="20" fill="#e4e6ea"/><circle cx="20" cy="16" r="7.5" fill="#bcc0c4"/><path d="M5 36.5C5 29 11.7 23 20 23s15 6 15 13.5" fill="#bcc0c4"/></svg>';

/** Quick reply suggestions */
const QUICK_REPLIES = [
  'Is this still available?',
  'Can we meet today?',
  'I\'ll take it!',
  'What\'s your lowest price?',
  'Can you deliver?',
  'Send more photos',
];

/** Conversations array */
let CONVS = [];

/** Messages keyed by conversation ID */
let msgs = {};

/** Currently active conversation object */
let activeConv = null;

/** Active tab filter: 'all' | 'buying' | 'selling' | 'unread' */
let activeTab = 'all';

/** Chat WebSocket instance */
let chatSocket = null;

/** Presence WebSocket instance */
let presenceSocket = null;

/** Online status map: userId -> 'online' | 'offline' */
const onlineStatus = {};

/** Voice note audio data map: stableId -> { url, duration, waveform } */
const vnAudioMap = {};

/** Currently playing voice note id */
let currentVnId = null;

/** Current audio element for voice playback */
let currentAudio = null;

/** Monotonic counter for local voice note IDs */
let vnCounter = 0;

/** Current user ID from Django context */
const currentUserId = parseInt(document.body.dataset.userId);

/** Voice note playback speed presets */
const VN_SPEEDS = [1, 1.5, 2, 0.5];

/** Reply state */
let replyIdx = null;
let replyCid = null;

/** Context menu state */
let ctxMsgIdx = null;
let ctxMsgCid = null;

/** Pending photos for upload */
let pendingPhotos = [];

/** Profile data cache for user profiles */
const UP_DATA = {};

/** Listing details cache */
const LISTING_DETAILS = {};

/** Recording state */
let mediaRecorder = null;
let recChunks = [];
let recStream = null;
let recTimerInterval = null;
let recSeconds = 0;
let analyserNode = null;
let audioCtxRec = null;
let animFrameRec = null;
let waveformAmps = [];

/** Typing indicator state */
let typingTimeout = null;
let _typingSent = false;
let _typingStopTimer = null;

/** Search debounce timer */
let _searchTimer = null;

/** Swipe-to-reply state */
let swipeStartX = 0;
let swipeStartY = 0;
let swipeTarget = null;
const swipeThreshold = 50;

/** Last scroll position for conversation list */
let lastConvY = 0;