/* ============================================
   KAVACH – Service Worker
   Network-first for pages, cache-first for assets
   ============================================ */

const CACHE_NAME = 'kavach-v6';
const STATIC_ASSETS = [
    '/css/styles.css',
    '/js/app.js',
    '/js/i18n.js',
    '/js/camera.js',
    '/js/screenshot.js',
    '/js/qrcode.js',
    '/js/url.js',
    '/manifest.json',
    '/icons/icon-192x192.png',
    '/icons/icon-512x512.png',
];

// Install: Cache static assets (but NOT the HTML page)
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(STATIC_ASSETS);
        })
    );
    self.skipWaiting();
});

// Activate: Clean ALL old caches immediately
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) => {
            return Promise.all(
                keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
            );
        })
    );
    self.clients.claim();
});

// Fetch: Network-first for pages & API, cache-first for static JS/CSS only
self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);

    // API calls: network-only
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(
            fetch(event.request).catch(() => {
                return new Response(
                    JSON.stringify({ error: 'Offline. Please check your connection.' }),
                    { headers: { 'Content-Type': 'application/json' } }
                );
            })
        );
        return;
    }

    // HTML pages (navigation): ALWAYS network-first
    if (event.request.mode === 'navigate' || event.request.destination === 'document') {
        event.respondWith(
            fetch(event.request).then((response) => {
                // Cache the latest HTML for offline fallback
                const clone = response.clone();
                caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
                return response;
            }).catch(() => {
                return caches.match(event.request) || caches.match('/');
            })
        );
        return;
    }

    // Static assets (JS/CSS): cache-first
    event.respondWith(
        caches.match(event.request).then((cached) => {
            return cached || fetch(event.request).then((response) => {
                if (response.status === 200) {
                    const clone = response.clone();
                    caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
                }
                return response;
            });
        }).catch(() => {
            if (event.request.mode === 'navigate') {
                return caches.match('/');
            }
        })
    );
});
