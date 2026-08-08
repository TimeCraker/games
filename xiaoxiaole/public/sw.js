// 桓睿消消乐 Service Worker v2.10 - 智能缓存 + 自动更新
const CACHE = 'xxl-v2.20';
const CORE_ASSETS = [
  './',
  './index.html',
  './styles.css',
  './game.js',
  './manifest.webmanifest',
  './assets/faces/face0.jpg',
  './assets/faces/face1.jpg',
  './assets/faces/face2.jpg',
  './assets/faces/face3.jpg',
  './assets/backgrounds/bg-anime-1.webp',
  './assets/backgrounds/bg-anime-2.webp',
  './assets/music/bgm1.mp3?v=2.16',
  './assets/music/bgm2.mp3?v=2.16',
  './assets/music/bgm3.mp3?v=2.16',
  './assets/music/bgm4.mp3?v=2.16',
];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(CORE_ASSETS)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return; // 只处理同源

  // 导航请求（HTML 入口）：network-first，保证总是拿到最新版本
  if (req.mode === 'navigate') {
    e.respondWith(
      fetch(req).then(res => {
        if (res && res.status === 200) {
          const clone = res.clone();
          caches.open(CACHE).then(c => c.put(req, clone));
        }
        return res;
      }).catch(() => caches.match(req).then(c => c || caches.match('./index.html')))
    );
    return;
  }

  // 静态资源：stale-while-revalidate（先返回缓存加速，后台更新）
  e.respondWith(
    caches.match(req).then(cached => {
      const fetcher = fetch(req).then(res => {
        if (res && res.status === 200 && res.type === 'basic') {
          const clone = res.clone();
          caches.open(CACHE).then(c => c.put(req, clone));
        }
        return res;
      }).catch(() => cached);
      return cached || fetcher;
    })
  );
});
