// Service worker do PWA Minhas Finanças
const CACHE = 'financas-v3';
const ARQUIVOS_ESTATICOS = [
  '/static/css/style.css',
  '/static/js/grafico.js',
  '/static/js/metas.js',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
  '/manifest.json',
  '/offline',
];

self.addEventListener('install', (evento) => {
  evento.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(ARQUIVOS_ESTATICOS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (evento) => {
  evento.waitUntil(
    caches.keys().then((chaves) =>
      Promise.all(chaves.filter((c) => c !== CACHE).map((c) => caches.delete(c)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (evento) => {
  const req = evento.request;
  if (req.method !== 'GET') return;

  // Páginas: rede primeiro (dados sempre atualizados), fallback offline
  if (req.mode === 'navigate') {
    evento.respondWith(
      fetch(req).catch(() =>
        caches.match(req).then((r) => r || caches.match('/offline'))
      )
    );
    return;
  }

  // Estáticos: cache primeiro, atualiza em segundo plano
  evento.respondWith(
    caches.match(req).then((emCache) => {
      const daRede = fetch(req)
        .then((resposta) => {
          if (resposta.ok) {
            const copia = resposta.clone();
            caches.open(CACHE).then((cache) => cache.put(req, copia));
          }
          return resposta;
        })
        .catch(() => emCache);
      return emCache || daRede;
    })
  );
});
