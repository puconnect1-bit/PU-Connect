/* PU-Connect Service Worker — no caching (pass-through) */
/* Push notifications only. Caching can be re-enabled later. */

self.addEventListener('install', event => {
  /* No caching — activate immediately */
  event.waitUntil(self.skipWaiting());
});

self.addEventListener('activate', event => {
  /* Purge any existing caches from previous versions */
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  /* Skip non-GET, cross-origin, WebSockets, admin */
  if (request.method !== 'GET') return;
  if (url.origin !== self.location.origin) return;
  if (url.pathname.startsWith('/admin/')) return;
  if (url.pathname.startsWith('/ws/')) return;

  /* Network-only — no caching */
  event.respondWith(fetch(request, { credentials: 'include' }));
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