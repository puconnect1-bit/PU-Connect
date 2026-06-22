/* PU-Connect Service Worker */
const CACHE_VERSION = 'pu-v1';
const STATIC_CACHE  = `${CACHE_VERSION}-static`;
const PAGE_CACHE    = `${CACHE_VERSION}-pages`;
const ALL_CACHES    = [STATIC_CACHE, PAGE_CACHE];

/* ── Static assets to pre-cache on install ── */
const STATIC_ASSETS = [
  '/static/manifest.json',
  '/static/Auth_app/css/auth.css',
  '/static/Base_app/css/index.css',
  '/static/Base_app/css/about.css',
  '/static/Base_app/css/help.css',
  '/static/Base_app/css/privacy.css',
  '/static/Base_app/css/safety.css',
  '/static/Base_app/css/terms.css',
  '/static/Listings_app/css/listings.css',
  '/static/Listings_app/css/create-listing.css',
  '/static/Listings_app/css/wishlist.css',
  '/static/Profile_app/css/profile.css',
  '/static/Profile_app/css/settings.css',
  '/static/Reels_app/css/reels.css',
  '/static/chat_app/css/chat.css',
  '/static/dash_app/css/dashboard.css',
  '/static/dash_app/css/dashboard-products.css',
  '/static/dash_app/css/dashboard-services.css',
  '/static/search_app/css/search.css',
];

/* ── App shell pages to pre-cache on install ── */
const APP_SHELL = [
  '/dashboard/',
  '/listings/',
  '/chat/',
  '/profile/',
  '/search/',
  '/offline/',
];

/* ─────────────────────────────────────────────
   INSTALL — fill caches
───────────────────────────────────────────── */
self.addEventListener('install', event => {
  event.waitUntil(
    Promise.all([
      caches.open(STATIC_CACHE).then(c => c.addAll(STATIC_ASSETS)),
      caches.open(PAGE_CACHE).then(c =>
        Promise.allSettled(APP_SHELL.map(url =>
          fetch(url, { credentials: 'include' })
            .then(r => { if (r.ok) c.put(url, r); })
            .catch(() => {})
        ))
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
   FETCH — cache strategy
───────────────────────────────────────────── */
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  /* Skip non-GET, cross-origin, and Django admin/API routes */
  if (request.method !== 'GET') return;
  if (url.origin !== self.location.origin) return;
  if (url.pathname.startsWith('/admin/')) return;
  if (url.pathname.startsWith('/api/') ||
      url.pathname.startsWith('/chat/api/') ||
      url.pathname.startsWith('/auth/api/') ||
      url.pathname.startsWith('/profile/api/') ||
      url.pathname.startsWith('/ws/')) return;

  /* Static assets — cache-first */
  if (url.pathname.startsWith('/static/')) {
    event.respondWith(
      caches.match(request).then(cached => cached || fetch(request).then(res => {
        if (res.ok) {
          const clone = res.clone();
          caches.open(STATIC_CACHE).then(c => c.put(request, clone));
        }
        return res;
      }))
    );
    return;
  }

  /* HTML pages — network-first, fall back to cache, then offline page */
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

  const title   = data.title   || 'PU-Connect';
  const body    = data.body    || 'You have a new notification';
  const icon    = data.icon    || '/static/icons/icon-192.png';
  const badge   = data.badge   || '/static/icons/icon-192.png';
  const url     = data.url     || '/chat/';
  const tag     = data.tag     || 'pu-notification';

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
