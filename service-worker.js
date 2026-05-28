/* Baste Travels Service Worker — v2026.2 */
const CACHE = 'baste-travels-v2026-2';
const STATIC = [
  '/',
  '/index.html',
  '/services.html',
  '/routes.html',
  '/about.html',
  '/contact.html',
  '/booking.html',
  '/offline.html',
  '/assets/css/style.css',
  '/assets/js/main.js',
  '/manifest.json'
];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(STATIC)).catch(() => {}));
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then((keys) => Promise.all(
    keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))
  )));
  self.clients.claim();
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);

  // HTML: network-first
  if (req.mode === 'navigate' || (req.headers.get('accept') || '').includes('text/html')) {
    e.respondWith(
      fetch(req).then((r) => {
        const clone = r.clone();
        caches.open(CACHE).then((c) => c.put(req, clone)).catch(() => {});
        return r;
      }).catch(() => caches.match(req).then((r) => r || caches.match('/offline.html')))
    );
    return;
  }

  // JS/CSS/JSON: network-first to ensure updated client code is loaded
  if (url.origin === location.origin && ['.js', '.css', '.json'].some((ext) => url.pathname.endsWith(ext))) {
    e.respondWith(
      fetch(req).then((r) => {
        if (r.ok) {
          const clone = r.clone();
          caches.open(CACHE).then((c) => c.put(req, clone)).catch(() => {});
        }
        return r;
      }).catch(() => caches.match(req).then((cached) => cached || new Response('Offline', { status: 503 })))
    );
    return;
  }

  // Static: cache-first
  e.respondWith(
    caches.match(req).then((cached) => cached || fetch(req).then((r) => {
      if (r.ok && url.origin === location.origin) {
        const clone = r.clone();
        caches.open(CACHE).then((c) => c.put(req, clone)).catch(() => {});
      }
      return r;
    }).catch(() => new Response('Offline', {status: 503})))
  );
});
