/* Банкарски имот — service worker
   Strategy:
   - App shell (html/css/js/icons): cache-first, so the app opens instantly and works offline.
   - Data (listings.json): network-first, so the Monday refresh is always shown when online,
     falling back to the last cached copy when offline.
   Bump CACHE_VERSION whenever the shell files change to force clients to update. */

const CACHE_VERSION = "imot-v1";
const SHELL_CACHE = CACHE_VERSION + "-shell";
const DATA_CACHE = CACHE_VERSION + "-data";

const SHELL_ASSETS = [
  "./",
  "./index.html",
  "./styles.css",
  "./app.js",
  "./manifest.webmanifest",
  "./icon-192.png",
  "./icon-512.png"
];

self.addEventListener("install", function (event) {
  event.waitUntil(
    caches.open(SHELL_CACHE).then(function (cache) {
      return cache.addAll(SHELL_ASSETS);
    }).then(function () {
      return self.skipWaiting();
    })
  );
});

self.addEventListener("activate", function (event) {
  event.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(
        keys.filter(function (k) {
          return k !== SHELL_CACHE && k !== DATA_CACHE;
        }).map(function (k) {
          return caches.delete(k);
        })
      );
    }).then(function () {
      return self.clients.claim();
    })
  );
});

self.addEventListener("fetch", function (event) {
  var req = event.request;
  if (req.method !== "GET") return;

  var url = new URL(req.url);

  // Data: network-first.
  if (url.pathname.indexOf("/data/listings.json") !== -1) {
    event.respondWith(
      fetch(req).then(function (res) {
        var copy = res.clone();
        caches.open(DATA_CACHE).then(function (cache) {
          cache.put("./data/listings.json", copy);
        });
        return res;
      }).catch(function () {
        return caches.match("./data/listings.json");
      })
    );
    return;
  }

  // Google Fonts: cache-first (stale-while-revalidate style).
  if (url.hostname.indexOf("fonts.googleapis.com") !== -1 ||
      url.hostname.indexOf("fonts.gstatic.com") !== -1) {
    event.respondWith(
      caches.open(SHELL_CACHE).then(function (cache) {
        return cache.match(req).then(function (cached) {
          var network = fetch(req).then(function (res) {
            cache.put(req, res.clone());
            return res;
          }).catch(function () { return cached; });
          return cached || network;
        });
      })
    );
    return;
  }

  // App shell + everything else same-origin: cache-first, fall back to network.
  if (url.origin === self.location.origin) {
    event.respondWith(
      caches.match(req).then(function (cached) {
        return cached || fetch(req).then(function (res) {
          return res;
        }).catch(function () {
          // Last resort for navigations: serve the app shell.
          if (req.mode === "navigate") return caches.match("./index.html");
        });
      })
    );
  }
});
