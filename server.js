const http = require('http');
const fs   = require('fs');
const path = require('path');

const PORT = Number(process.argv[2] || process.env.PORT || 4321);
const ROOT = __dirname;

const mime = {
  '.html': 'text/html; charset=utf-8',
  '.css':  'text/css; charset=utf-8',
  '.js':   'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png':  'image/png',
  '.jpg':  'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.webp': 'image/webp',
  '.svg':  'image/svg+xml',
  '.ico':  'image/x-icon',
  '.woff': 'font/woff',
  '.woff2':'font/woff2',
  '.mp4':  'video/mp4',
};

http.createServer((req, res) => {
  const url = decodeURIComponent(req.url.split('?')[0]);
  let filePath = path.join(ROOT, url === '/' ? 'index.html' : url);
  if (!filePath.startsWith(ROOT)) { res.writeHead(403); res.end('Forbidden'); return; }

  fs.stat(filePath, (err, st) => {
    if (err) { res.writeHead(404); res.end('Not found: ' + url); return; }
    // Un répertoire doit être re-stat après avoir résolu son index, sinon
    // Content-Length porte la taille du dossier et la réponse est tronquée.
    if (st.isDirectory()) {
      filePath = path.join(filePath, 'index.html');
      fs.stat(filePath, (e2, st2) => (e2 ? (res.writeHead(404), res.end('Not found')) : serve(st2)));
      return;
    }
    serve(st);

    function serve(stat) {
      const ext  = path.extname(filePath).toLowerCase();
      const type = mime[ext] || 'application/octet-stream';
      // Les médias sont figés : les laisser en cache évite de re-télécharger
      // ~9 Mo à chaque rechargement, et permet aux partiels 206 d'être réutilisés
      // quand on remonte sur une séquence déjà vue. Le HTML, lui, doit être frais.
      const cache = filePath.includes(path.sep + 'assets' + path.sep)
        ? 'public, max-age=86400'
        : 'no-store';
      const head = { 'Content-Type': type, 'Accept-Ranges': 'bytes', 'Cache-Control': cache };

      // Les vidéos de v4.x sont scrubbées au scroll, donc seekées en continu.
      // Sans Range, le navigateur les traite comme non-seekables et le scrub
      // dépend du buffer complet : on répond en 206 dès que c'est demandé.
      const range = (req.headers.range || '').trim();
      if (/^bytes=\d*-\d*$/.test(range)) {
        const [rawStart, rawEnd] = range.replace('bytes=', '').split('-');
        const start = rawStart ? parseInt(rawStart, 10) : 0;
        const end   = rawEnd   ? parseInt(rawEnd, 10)   : stat.size - 1;
        if (start > end || end >= stat.size) {
          res.writeHead(416, { 'Content-Range': `bytes */${stat.size}` });
          res.end();
          return;
        }
        res.writeHead(206, Object.assign({}, head, {
          'Content-Range': `bytes ${start}-${end}/${stat.size}`,
          'Content-Length': end - start + 1,
        }));
        fs.createReadStream(filePath, { start, end }).pipe(res);
        return;
      }

      res.writeHead(200, Object.assign({}, head, { 'Content-Length': stat.size }));
      fs.createReadStream(filePath).pipe(res);
    }
  });
}).listen(PORT, () => console.log(`ACME site on http://localhost:${PORT}`));
