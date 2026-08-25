const http = require('http');
const fs   = require('fs');
const path = require('path');

const PORT = Number(process.argv[2]) || 4321;   // `node server.js 4326` pour cohabiter avec une autre version
const ROOT = __dirname;

const mime = {
  '.html': 'text/html; charset=utf-8',
  '.css':  'text/css; charset=utf-8',
  '.js':   'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png':  'image/png',
  '.jpg':  'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.svg':  'image/svg+xml',
  '.ico':  'image/x-icon',
  '.webp': 'image/webp',
  '.woff': 'font/woff',
  '.woff2':'font/woff2',
  '.mp4':  'video/mp4',
  '.webm': 'video/webm',
};

http.createServer((req, res) => {
  const url = decodeURIComponent(req.url.split('?')[0]);
  let filePath = path.join(ROOT, url === '/' ? 'index.html' : url);
  if (!filePath.startsWith(ROOT)) { res.writeHead(403); res.end('Forbidden'); return; }
  fs.stat(filePath, (err, stat) => {
    if (err) { res.writeHead(404); res.end('Not found: ' + url); return; }
    if (stat.isDirectory()) {
      filePath = path.join(filePath, 'index.html');
      try { stat = fs.statSync(filePath); }
      catch (e) { res.writeHead(404); res.end('Not found'); return; }
    }
    const ext  = path.extname(filePath).toLowerCase();
    const type = mime[ext] || 'application/octet-stream';
    const total = stat.size;
    const range = req.headers.range;

    // Requêtes Range (nécessaires au scrub vidéo : le navigateur cherche une position)
    if (range) {
      const m = /bytes=(\d*)-(\d*)/.exec(range);
      let start = m && m[1] ? parseInt(m[1], 10) : 0;
      let end   = m && m[2] ? parseInt(m[2], 10) : total - 1;
      if (isNaN(start) || isNaN(end) || start > end || end >= total) {
        res.writeHead(416, { 'Content-Range': `bytes */${total}` });
        res.end();
        return;
      }
      res.writeHead(206, {
        'Content-Type': type,
        'Content-Range': `bytes ${start}-${end}/${total}`,
        'Accept-Ranges': 'bytes',
        'Content-Length': end - start + 1,
        'Cache-Control': 'no-store',
      });
      fs.createReadStream(filePath, { start, end }).pipe(res);
      return;
    }

    res.writeHead(200, {
      'Content-Type': type,
      'Content-Length': total,
      'Accept-Ranges': 'bytes',
      'Cache-Control': 'no-store',
    });
    fs.createReadStream(filePath).pipe(res);
  });
}).listen(PORT, () => console.log(`ACME site on http://localhost:${PORT}`));
