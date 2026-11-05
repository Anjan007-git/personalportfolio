const http = require('http');
const fs = require('fs');
const path = require('path');
const url = require('url');

const PORT = process.env.PORT || 3000;
const PUBLIC_DIR = path.join(__dirname, 'cloned_site');

// Load image cache map
let imageMap = {};
const mapPath = path.join(PUBLIC_DIR, 'next_image_map.json');
if (fs.existsSync(mapPath)) {
  try {
    imageMap = JSON.parse(fs.readFileSync(mapPath, 'utf8'));
  } catch (e) {
    console.error('Error loading next_image_map.json:', e);
  }
}

const MIME_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.webmanifest': 'application/manifest+json; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.webp': 'image/webp',
  '.avif': 'image/avif',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
  '.ttf': 'font/ttf',
  '.pdf': 'application/pdf',
  '.rsc': 'text/x-component; charset=utf-8',
  '.txt': 'text/plain; charset=utf-8'
};

function sendFile(res, filePath, contentType) {
  fs.stat(filePath, (err, stats) => {
    if (err || !stats.isFile()) {
      res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
      res.end('404 Not Found');
      return;
    }

    const ext = path.extname(filePath).toLowerCase();
    const mime = contentType || MIME_TYPES[ext] || 'application/octet-stream';

    res.writeHead(200, {
      'Content-Type': mime,
      'Content-Length': stats.size,
      'Access-Control-Allow-Origin': '*',
      'Cache-Control': ext === '.html' ? 'no-cache' : 'public, max-age=31536000, immutable'
    });

    const stream = fs.createReadStream(filePath);
    stream.pipe(res);
  });
}

const server = http.createServer((req, res) => {
  const parsedUrl = url.parse(req.url, true);
  let pathname = decodeURIComponent(parsedUrl.pathname);

  // 0. Handle POST (e.g. Contact Form Server Action)
  if (req.method === 'POST') {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      console.log(`Received contact form submission on ${pathname}:`, body);
      // Append to submissions log
      try {
        const entry = { date: new Date().toISOString(), path: pathname, data: body };
        fs.appendFileSync(path.join(__dirname, 'contact_submissions.jsonl'), JSON.stringify(entry) + '\n');
      } catch (e) {}

      // Return Next.js App Router action response
      res.writeHead(200, {
        'Content-Type': 'text/x-component; charset=utf-8',
        'Access-Control-Allow-Origin': '*'
      });
      res.end('0:{"a":{"ok":true},"f":[]}\n');
    });
    return;
  }

  // 1. Handle opengraph-image
  if (pathname === '/opengraph-image' || pathname.startsWith('/opengraph-image')) {
    const ogPath = path.join(PUBLIC_DIR, 'opengraph-image.png');
    if (fs.existsSync(ogPath)) {
      return sendFile(res, ogPath, 'image/png');
    }
  }

  // 2. Handle Next.js image optimizer requests
  if (pathname === '/_next/image') {
    const rawUrl = req.url;
    // Check in imageMap
    if (imageMap[rawUrl]) {
      const cachedFile = path.join(PUBLIC_DIR, imageMap[rawUrl]);
      if (fs.existsSync(cachedFile)) {
        return sendFile(res, cachedFile);
      }
    }
    // Try unescaped or alternative matches
    const imgParam = parsedUrl.query.url;
    if (imgParam) {
      const decodedImg = decodeURIComponent(imgParam);
      // Look for original asset
      const directPath = path.join(PUBLIC_DIR, decodedImg.replace(/^\//, ''));
      if (fs.existsSync(directPath)) {
        return sendFile(res, directPath);
      }
    }
  }

  // 2. Handle RSC requests (Next.js App Router client navigation)
  const isRSC = req.headers['rsc'] === '1' || parsedUrl.query._rsc !== undefined;
  if (isRSC) {
    let rscRel = pathname === '/' ? 'index.rsc' : pathname.replace(/^\//, '') + '.rsc';
    let rscPath = path.join(PUBLIC_DIR, rscRel);
    if (fs.existsSync(rscPath)) {
      return sendFile(res, rscPath, 'text/x-component; charset=utf-8');
    }
  }

  // Normalize path
  if (pathname === '/') {
    pathname = '/index.html';
  }

  let localPath = path.join(PUBLIC_DIR, pathname.replace(/^\//, ''));

  // If path exists and is a file
  if (fs.existsSync(localPath) && fs.statSync(localPath).isFile()) {
    return sendFile(res, localPath);
  }

  // If directory, look for index.html
  if (fs.existsSync(localPath) && fs.statSync(localPath).isDirectory()) {
    const indexHtml = path.join(localPath, 'index.html');
    if (fs.existsSync(indexHtml)) {
      return sendFile(res, indexHtml);
    }
  }

  // Try appending .html (clean URL support)
  const htmlPath = localPath + '.html';
  if (fs.existsSync(htmlPath) && fs.statSync(htmlPath).isFile()) {
    return sendFile(res, htmlPath);
  }

  // If path has encoded or decoded [slug]
  if (pathname.includes('[slug]')) {
    const encPath = path.join(PUBLIC_DIR, pathname.replace('[slug]', '%5Bslug%5D').replace(/^\//, ''));
    if (fs.existsSync(encPath)) {
      return sendFile(res, encPath);
    }
  }

  // Only fallback to index.html for page navigations (not for static assets or _next)
  if (!pathname.startsWith('/_next/') && !path.extname(pathname)) {
    const fallback = path.join(PUBLIC_DIR, 'index.html');
    if (fs.existsSync(fallback)) {
      return sendFile(res, fallback);
    }
  }

  res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
  res.end('404 Not Found');
});

server.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
});
