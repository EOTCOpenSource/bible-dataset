/* Offline support for the reader.
   - The page itself: network first, so updates show up right away.
   - Catalogs, book files, fonts and assets: served from cache, refreshed in
     the background. Chapters you have read stay readable offline. */
const VERSION = 'reader-v1';
const SHELL = [
  './', 'index.html', 'assets/app.css', 'assets/app.js', 'manifest.webmanifest',
  'assets/logo-180.png', 'assets/favicon-32.png', 'assets/icon-192.png',
  'translations.json', 'books.json', 'apocrypha_books.json',
];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(VERSION).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== VERSION).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  const sameOrigin = url.origin === self.location.origin;
  const isFont = /fonts\.(googleapis|gstatic)\.com$/.test(url.hostname);
  if (!sameOrigin && !isFont) return;

  // The page and the app's own code: network first, so updates arrive at once.
  const isPage = req.mode === 'navigate' ||
    (sameOrigin && /(\/|index\.html|app\.(js|css)|\.webmanifest)$/.test(url.pathname));
  if (isPage) {
    e.respondWith(
      fetch(req)
        .then((res) => { const copy = res.clone(); caches.open(VERSION).then((c) => c.put(req, copy)); return res; })
        .catch(() => caches.match(req).then((r) => r || caches.match('index.html'))),
    );
    return;
  }

  e.respondWith(
    caches.open(VERSION).then(async (cache) => {
      const cached = await cache.match(req);
      const fresh = fetch(req)
        .then((res) => { if (res.ok || res.type === 'opaque') cache.put(req, res.clone()); return res; })
        .catch(() => cached);
      return cached || fresh;
    }),
  );
});
