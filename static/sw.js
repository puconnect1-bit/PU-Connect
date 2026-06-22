/* PU-Connect Service Worker */
const CACHE_VERSION = 'pu-v3';
const STATIC_CACHE  = `${CACHE_VERSION}-static`;
const PAGE_CACHE    = `${CACHE_VERSION}-pages`;
const API_CACHE     = `${CACHE_VERSION}-api`;
const IMG_CACHE     = `${CACHE_VERSION}-img`;
const ALL_CACHES    = [STATIC_CACHE, PAGE_CACHE, API_CACHE, IMG_CACHE];

/* ── Static assets to pre-cache on install ── */
const STATIC_ASSETS = [
  /* Design system */
  '/static/Base_app/css/tokens.css',
  '/static/Base_app/css/shell.css',

  /* Public pages */
  '/static/Base_app/css/index.css',
  '/static/Base_app/css/about.css',
  '/static/Base_app/css/help.css',
  '/static/Base_app/css/privacy.css',
  '/static/Base_app/css/safety.css',
  '/static/Base_app/css/terms.css',

  /* App pages */
  '/static/Auth_app/css/auth.css',
  '/static/dash_app/css/dashboard.css',
  '/static/chat_app/css/chat.css',
  '/static/Profile_app/css/profile.css',
  '/static/Listings_app/css/listings.css',
  '/static/Listings_app/css/create-listing.css',
  '/static/Listings_app/css/wishlist.css',
  '/static/search_app/css/search.css',
  '/static/Reels_app/css/reels.css',

  /* JS */
  '/static/Base_app/js/notifications.js',

  /* Icons — critical for install prompt & splash */
  '/static/icons/logo.png',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
  '/static/icons/icon-maskable-192.png',
  '/static/icons/icon-maskable-512.png',
  '/static/icons/apple-touch-icon.png',
  '/static/icons/favicon.ico',

  /* Manifest */
  '/static/manifest.json',
];

/* ── App shell HTML pages ── */
const APP_SHELL = [
  '/dashboard/',
  '/listings/',
  '/chat/',
  '/profile/',
  '/search/',
  '/offline/',
];

/* ── API routes to stale-while-revalidate ── */
const SWR_ROUTES = [
  '/dashboard/api/listings/',
  '/profile/api/me/',
  '/profile/api/verification/info/',
];

/* ─────────────────────────────────────────────
   INSTALL — fill caches
───────────────────────────────────────────── */
self.addEventListener('install', event => {
  event.waitUntil(
    Promise.all([
      /* Pre-cache static assets — skip failures so install always succeeds */
      caches.open(STATIC_CACHE).then(cache =>
        Promise.allSettled(
          STATIC_ASSETS.map(url =>
            cache.add(url).catch(() => {})
          )
        )
      ),
      /* Pre-cache app shell pages */
      caches.open(PAGE_CACHE).then(cache =>
        Promise.allSettled(
          APP_SHELL.map(url =>
            fetch(url, { credentials: 'include' })
              .then(r => { if (r.ok) cache.put(url, r); })
              .catch(() => {})
          )
        )
      ),
    ]).then(() => self.skipWaiting())
  );
});

/* ─────────────────────────────────────────────
   ACTIVATE — purge old caches
───────────────────────────────────────────── */
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys.filter(k => !ALL_CACHES.includes(k)).map(k => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

/* ─────────────────────────────────────────────
   FETCH — routing strategies
───────────────────────────────────────────── */
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  /* Skip non-GET, cross-origin, WebSockets, admin */
  if (request.method !== 'GET') return;
  if (url.origin !== self.location.origin) return;
  if (url.pathname.startsWith('/admin/')) return;
  if (url.pathname.startsWith('/ws/')) return;

  /* Skip write-side API routes (auth, chat, mutations) */
  const SKIP_API = [
    '/auth/api/', '/chat/api/', '/profile/api/change-password',
    '/profile/api/update/', '/profile/api/follow/', '/profile/api/report/',
    '/profile/api/verification/apply/', '/profile/api/verification/paid/',
    '/profile/api/verification/submit-docs/', '/listings/api/create/',
    '/listings/api/delete/', '/listings/api/toggle-status/',
    '/api/r2-upload/',
  ];
  if (SKIP_API.some(p => url.pathname.startsWith(p))) return;

  /* ── 1. Static assets — cache-first, populate on miss ── */
  if (url.pathname.startsWith('/static/')) {
    event.respondWith(
      caches.match(request).then(cached => {
        if (cached) return cached;
        return fetch(request).then(res => {
          if (res.ok) {
            const clone = res.clone();
            caches.open(STATIC_CACHE).then(c => c.put(request, clone));
          }
          return res;
        });
      })
    );
    return;
  }

  /* ── 2. External images (R2 / CDN) — cache-first with 7-day TTL ── */
  if (url.origin !== self.location.origin &&
      /\.(jpe?g|png|webp|gif|svg)$/i.test(url.pathname)) {
    event.respondWith(
      caches.open(IMG_CACHE).then(cache =>
        cache.match(request).then(cached => {
          if (cached) return cached;
          return fetch(request).then(res => {
            if (res.ok) cache.put(request, res.clone());
            return res;
          }).catch(() => cached);
        })
      )
    );
    return;
  }

  /* ── 3. SWR API routes — instant from cache, refresh in background ── */
  if (SWR_ROUTES.some(r => url.pathname === r || url.pathname.startsWith(r))) {
    event.respondWith(
      caches.open(API_CACHE).then(cache =>
        cache.match(request).then(cached => {
          const networkFetch = fetch(request, { credentials: 'include' })
            .then(res => {
              if (res.ok) cache.put(request, res.clone());
              return res;
            })
            .catch(() => cached);
          return cached || networkFetch;
        })
      )
    );
    return;
  }

  /* ── 4. HTML pages — network-first, cache fallback, then /offline/ ── */
  if (request.headers.get('Accept')?.includes('text/html')) {
    event.respondWith(
      fetch(request, { credentials: 'include' })
        .then(res => {
          if (res.ok) {
            const clone = res.clone();
            caches.open(PAGE_CACHE).then(c => c.put(request, clone));
          }
          return res;
        })
        .catch(() =>
          caches.match(request).then(cached =>
            cached || caches.match('/offline/')
          )
        )
    );
    return;
  }
});

/* ─────────────────────────────────────────────
   PUSH — show notification
───────────────────────────────────────────── */
self.addEventListener('push', event => {
  let data = {};
  try { data = event.data ? event.data.json() : {}; } catch (e) {}

  const title = data.title || 'PU Connect';
  const body  = data.body  || 'You have a new notification';
  const icon  = data.icon  || '/static/icons/icon-192.png';
  const badge = data.badge || '/static/icons/icon-96.png';
  const url   = data.url   || '/chat/';
  const tag   = data.tag   || 'pu-notification';

  event.waitUntil(
    self.registration.showNotification(title, {
      body,
      icon,
      badge,
      tag,
      data: { url },
      vibrate: [100, 50, 100],
      requireInteraction: false,
    })
  );
});

/* ─────────────────────────────────────────────
   NOTIFICATION CLICK — open / focus the app
───────────────────────────────────────────── */
self.addEventListener('notificationclick', event => {
  event.notification.close();
  const targetUrl = event.notification.data?.url || '/chat/';

  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then(clients => {
        for (const client of clients) {
          if (client.url.includes(targetUrl) && 'focus' in client) {
            return client.focus();
          }
        }
        return self.clients.openWindow(targetUrl);
      })
  );
});
