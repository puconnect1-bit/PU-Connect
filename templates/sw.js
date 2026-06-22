const CACHE_NAME = 'pu-market-v1';
const urlsToCache = [
  '/',
  '/dashboard/dashboard/',
  '/static/dash_app/css/dashboard.css'
];

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(urlsToCache)));
});

self.addEventListener('fetch', event => {
  event.respondWith(caches.match(event.request).then(response => response || fetch(event.request)));
});

// Push notification listener
self.addEventListener('push', event => {
  let data = {};
  if (event.data) {
    try {
      data = event.data.json();
    } catch (e) {
      data = { title: 'PU-Connect Notification', body: event.data.text() };
    }
  }

  const title = data.title || 'New Notification';
  const options = {
    body: data.body || '',
    icon: data.icon || '/static/icons/logo-192.png',
    badge: data.badge || '/static/icons/logo-192.png',
    data: data.data || { url: '/dashboard/dashboard/' }
  };

  event.waitUntil(
    self.registration.showNotification(title, options)
  );
});

// Notification click handler
self.addEventListener('notificationclick', event => {
  event.notification.close();
  
  let targetUrl = '/dashboard/dashboard/';
  if (event.notification.data && event.notification.data.url) {
    targetUrl = event.notification.data.url;
  }
  
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(clientList => {
      // If there is already a window open with that URL, focus it
      for (const client of clientList) {
        if (client.url === targetUrl && 'focus' in client) {
          return client.focus();
        }
      }
      // Otherwise open a new window
      if (clients.openWindow) {
        return clients.openWindow(targetUrl);
      }
    })
  );
});
