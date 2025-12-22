const CACHE = "pars-wms-v1";
const ASSETS = [
  "/", "/dashboard", "/qr-page",
  "/static/manifest.json",
  "/static/qr_camera.js"
];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)));
});

self.addEventListener("fetch", (e) => {
  e.respondWith(
    caches.match(e.request).then(r => r || fetch(e.request))
  );
});
