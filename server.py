import http.server
import socketserver
import os
import urllib.parse
import json

PORT = int(os.environ.get("PORT", 3000))
PUBLIC_DIR = os.path.abspath("cloned_site")

image_map = {}
map_file = os.path.join(PUBLIC_DIR, "next_image_map.json")
if os.path.exists(map_file):
    try:
        with open(map_file, "r", encoding="utf-8") as f:
            image_map = json.load(f)
    except Exception as e:
        print("Error loading image map:", e)

MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".webmanifest": "application/manifest+json; charset=utf-8",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".avif": "image/avif",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
    ".woff": "font/woff",
    ".woff2": "font/woff2",
    ".ttf": "font/ttf",
    ".pdf": "application/pdf",
    ".rsc": "text/x-component; charset=utf-8",
    ".txt": "text/plain; charset=utf-8",
}

class CloneHandler(http.server.BaseHTTPRequestHandler):
    def send_file(self, file_path, content_type=None):
        try:
            with open(file_path, "rb") as f:
                data = f.read()
            ext = os.path.splitext(file_path)[1].lower()
            ct = content_type or MIME_TYPES.get(ext, "application/octet-stream")
            self.send_response(200)
            self.send_header("Content-Type", ct)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:
            self.send_error(500, str(e))

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8', errors='ignore')
        print(f"Received form submission on {self.path}: {body}")
        try:
            with open("contact_submissions.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps({"path": self.path, "data": body}) + "\n")
        except Exception:
            pass
        response_body = b'0:{"a":{"ok":true},"f":[]}\n'
        self.send_response(200)
        self.send_header("Content-Type", "text/x-component; charset=utf-8")
        self.send_header("Content-Length", str(len(response_body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(response_body)

    def do_GET(self):
        parsed = urllib.parse.urlsplit(self.path)
        pathname = urllib.parse.unquote(parsed.path)

        # 1. Handle opengraph-image
        if pathname == "/opengraph-image" or pathname.startswith("/opengraph-image"):
            og_path = os.path.join(PUBLIC_DIR, "opengraph-image.png")
            if os.path.exists(og_path):
                return self.send_file(og_path, "image/png")

        # 2. Handle Next.js image queries
        if pathname == "/_next/image":
            # Check map
            if self.path in image_map:
                cpath = os.path.join(PUBLIC_DIR, image_map[self.path].replace("/", os.sep))
                if os.path.exists(cpath):
                    return self.send_file(cpath)
            # Fallback to source
            qs = urllib.parse.parse_qs(parsed.query)
            if "url" in qs:
                src_url = urllib.parse.unquote(qs["url"][0]).lstrip("/")
                direct_path = os.path.join(PUBLIC_DIR, src_url.replace("/", os.sep))
                if os.path.exists(direct_path):
                    return self.send_file(direct_path)

        # 2. Handle RSC header
        is_rsc = self.headers.get("RSC") == "1" or "_rsc" in parsed.query
        if is_rsc:
            rsc_name = "index.rsc" if pathname == "/" else pathname.lstrip("/") + ".rsc"
            rsc_path = os.path.join(PUBLIC_DIR, rsc_name.replace("/", os.sep))
            if os.path.exists(rsc_path):
                return self.send_file(rsc_path, "text/x-component; charset=utf-8")

        # 3. Static routing
        target = "index.html" if pathname == "/" else pathname.lstrip("/")
        local_path = os.path.join(PUBLIC_DIR, target.replace("/", os.sep))

        if os.path.isfile(local_path):
            return self.send_file(local_path)

        if os.path.isdir(local_path):
            index_path = os.path.join(local_path, "index.html")
            if os.path.isfile(index_path):
                return self.send_file(index_path)

        # Clean URL
        if os.path.isfile(local_path + ".html"):
            return self.send_file(local_path + ".html")

        # Only fallback to index.html for page navigation (not static assets or _next)
        if not pathname.startswith("/_next/") and not os.path.splitext(pathname)[1]:
            fb = os.path.join(PUBLIC_DIR, "index.html")
            if os.path.isfile(fb):
                return self.send_file(fb)

        self.send_error(404, "File Not Found")

class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True

if __name__ == "__main__":
    with ThreadingHTTPServer(("", PORT), CloneHandler) as httpd:
        print(f"Python Server running at http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")
