/* Meowls e-Visa Service Worker
 * - Offline shell cache
 * - Push notification handler
 * - Notification click -> focus / open app
 */
const CACHE_NAME = 'meowls-evisa-v1';
const APP_SHELL = [
  '/',
  '/manifest.json',
  '/icon-192.png',
  '/icon-512.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL)).catch(() => {})
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

/* Network-first for API, cache-first for static */
self.addEventListener('fetch', (event) => {
  const { request } = event;
  if (request.method !== 'GET') return;
  const url = new URL(request.url);

  // Never cache API requests
  if (url.pathname.startsWith('/api/')) return;

  // Cache-first for same-origin static
  if (url.origin === self.location.origin) {
    event.respondWith(
      caches.match(request).then((cached) => {
        return (
          cached ||
          fetch(request)
            .then((resp) => {
              if (resp && resp.status === 200 && resp.type === 'basic') {
                const copy = resp.clone();
                caches.open(CACHE_NAME).then((c) => c.put(request, copy));
              }
              return resp;
            })
            .catch(() => cached)
        );
      })
    );
  }
});

/* Push event */
self.addEventListener('push', (event) => {
  let payload = {};
  try {
    payload = event.data ? event.data.json() : {};
  } catch (e) {
    payload = { title: 'Meowls e-Visa', body: event.data ? event.data.text() : '' };
  }
  const title = payload.title || 'Meowls e-Visa';
  const options = {
    body: payload.body || '',
    icon: '/icon-192.png',
    badge: '/icon-192.png',
    tag: payload.application_id || 'meowls-evisa',
    data: payload,
    vibrate: [180, 80, 180],
    requireInteraction: payload.status === 'approved'
  };
  event.waitUntil(self.registration.showNotification(title, options));
});

/* Notification click — focus or open the app to the application's detail page */
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const appId = event.notification?.data?.application_id;
  const targetUrl = appId ? `/applications/${appId}` : '/dashboard';
  event.waitUntil(
    self.clients
      .matchAll({ type: 'window', includeUncontrolled: true })
      .then((clientList) => {
        for (const client of clientList) {
          if ('focus' in client) {
            client.focus();
            if ('navigate' in client) {
              try {
                client.navigate(targetUrl);
              } catch (_) {}
            }
            return;
          }
        }
        if (self.clients.openWindow) return self.clients.openWindow(targetUrl);
      })
  );
});
