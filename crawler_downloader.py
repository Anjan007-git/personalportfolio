import os
import sys
import urllib.request
import urllib.parse
import re
from bs4 import BeautifulSoup
import hashlib
import json

BASE_URL = "https://tanishbhavsar.vercel.app"
DEST_DIR = os.path.abspath("cloned_site")

os.makedirs(DEST_DIR, exist_ok=True)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

def clean_rel_path(path_str):
    p = path_str.strip().strip("'\"`\\").replace("\\", "/")
    p = p.split("?")[0].split("#")[0]
    return p

def fetch_url(url, as_bytes=False, extra_headers=None):
    req_headers = dict(headers)
    if extra_headers:
        req_headers.update(extra_headers)
    req = urllib.request.Request(url, headers=req_headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
            return data if as_bytes else data.decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def save_file(rel_path, content):
    rel_path = clean_rel_path(rel_path).lstrip("/")
    clean_unquoted = urllib.parse.unquote(rel_path)
    full_path = os.path.join(DEST_DIR, clean_unquoted.replace("/", os.sep))
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "wb") as f:
        f.write(content)
    return full_path

print("Starting deep clone of", BASE_URL)

PAGES = [
    "/",
    "/about",
    "/contact",
    "/work",
    "/work/ajinkya-jadhav-photography",
    "/work/credzen",
    "/work/mediq",
    "/work/rapid-crisis-response"
]

all_assets = set()
all_next_images = set()

# 1. Download HTML pages
for p in PAGES:
    full_url = BASE_URL + p
    print(f"Fetching page: {p}")
    html_content = fetch_url(full_url, as_bytes=False)
    if html_content:
        # Save HTML
        if p == "/":
            save_file("index.html", html_content.encode("utf-8"))
        else:
            save_file(p.strip("/") + "/index.html", html_content.encode("utf-8"))
            save_file(p.strip("/") + ".html", html_content.encode("utf-8"))

        # Parse HTML for assets
        soup = BeautifulSoup(html_content, "html.parser")
        for tag in soup.find_all(True):
            for attr in ["src", "href", "poster", "data-src"]:
                val = tag.get(attr)
                if val and not val.startswith(("data:", "mailto:", "tel:", "javascript:", "#")):
                    if val.startswith("http://") or val.startswith("https://"):
                        if val.startswith(BASE_URL):
                            val = val[len(BASE_URL):]
                        else:
                            continue
                    if val.startswith("/_next/image?"):
                        all_next_images.add(val)
                    elif val.startswith("/"):
                        all_assets.add(clean_rel_path(val))

        # Regex search for assets in flight data and scripts
        regex_assets = re.findall(r'["\'](/_next/[^"\'\s>\\)]+|/(?:icons|desktop|hands|mockups-projects|media)/[^"\'\s>\\)]+\.[a-zA-Z0-9]+)["\']', html_content)
        for r_ast in regex_assets:
            if r_ast.startswith("/_next/image?"):
                all_next_images.add(r_ast)
            elif not r_ast.endswith("/"):
                all_assets.add(clean_rel_path(r_ast))

# 2. Download RSC payloads
for p in PAGES:
    rsc_path = "/index.rsc" if p == "/" else p.rstrip("/") + ".rsc"
    rsc_url = BASE_URL + rsc_path
    print(f"Fetching RSC: {rsc_path}")
    data = fetch_url(rsc_url, as_bytes=True)
    if data:
        save_file(rsc_path.lstrip("/"), data)
        try:
            rsc_str = data.decode("utf-8", errors="ignore")
            for m in re.findall(r'["\'](/_next/[^"\'\s>\\)]+|/(?:icons|desktop|hands|mockups-projects|media)/[^"\'\s>\\)]+\.[a-zA-Z0-9]+)["\']', rsc_str):
                if m.startswith("/_next/image?"):
                    all_next_images.add(m)
                elif not m.endswith("/"):
                    all_assets.add(clean_rel_path(m))
        except Exception:
            pass

# 3. Known static assets
known_files = [
    "/manifest.webmanifest",
    "/favicon.ico",
    "/icon.png",
    "/apple-icon.png",
    "/tanish-bhavsar-cv.pdf",
    "/tanish-bhavsar.jpg",
    "/desktop/avatar.webp",
    "/desktop/macbook.webp",
    "/desktop/wallpaper.webp",
    "/hands/left-hand.png",
    "/hands/right-hand.png",
    "/icons/Finder_Icon_macOS_Tahoe.png",
    "/icons/app-arduino.png",
    "/icons/app-blender.png",
    "/icons/app-cplusplus.png",
    "/icons/app-docker.png",
    "/icons/app-elevenlabs.png",
    "/icons/app-fastapi.png",
    "/icons/app-firebase.png",
    "/icons/app-gemini.png",
    "/icons/app-github.png",
    "/icons/app-mongodb.png",
    "/icons/app-nextjs.png",
    "/icons/app-nodejs.png",
    "/icons/app-opencv.png",
    "/icons/app-postgresql.png",
    "/icons/app-python.png",
    "/icons/app-pytorch.png",
    "/icons/app-raspberrypi.png",
    "/icons/app-react.png",
    "/icons/app-tensorflow.png",
    "/icons/app-typescript.png",
    "/icons/claude.svg",
    "/icons/figma.svg",
    "/icons/framer.avif",
    "/icons/github.svg",
    "/icons/javascript.svg",
    "/icons/langchain.svg",
    "/icons/leetcode.svg",
    "/icons/photoshop.avif",
    "/icons/webflow.avif",
    "/mockups-projects/Codex Image Aug 23, 2026, 06_05_05 PM.png",
    "/mockups-projects/Generated image 1 (5).png",
    "/mockups-projects/mockup-2.png",
    "/mockups-projects/mockup1.png",
    "/mockups-projects/siri-cover.jpg",
    "/mockups-projects/new/ChatGPT Image 11 Oct 2026, 18_24_05.png",
    "/mockups-projects/new/ChatGPT Image 11 Oct 2026, 18_28_16.png",
    "/mockups-projects/new/ChatGPT Image 11 Oct 2026, 18_35_02.png",
    "/mockups-projects/new/ChatGPT Image 11 Oct 2026, 18_35_15.png",
    "/mockups-projects/new/ChatGPT Image 11 Oct 2026, 18_35_46.png",
    "/mockups-projects/new/ChatGPT Image 11 Oct 2026, 18_39_51.png",
    "/mockups-projects/new/ChatGPT Image 11 Oct 2026, 18_45_59.png",
    "/mockups-projects/new/previsv2.png",
    "/_next/static/media/hero-portfolio.83853bb7.png",
    "/_next/static/media/Blue Rim Light Portrait.c4a95cbb.png",
    "/_next/static/media/tanish-card.d1f0a3aa.png",
    "/_next/static/media/7d4881bb7e1bf84d-s.p.woff2",
    "/_next/static/media/9cc5b37ab1350db7-s.p.woff2",
    "/_next/static/media/e4af272ccee01ff0-s.p.woff2",
    "/_next/static/media/e6099e249fd938cc-s.p.woff2",
    "/_next/static/media/ef0360dcf38d5c82-s.p.woff2",
    "/_next/static/css/21f01898705a7723.css",
    "/_next/static/css/3900e63377b5d53e.css",
    "/_next/static/css/69bec84043e722a7.css",
    "/_next/static/chunks/1255-0046eeb68b7d2d4d.js",
    "/_next/static/chunks/2014-cfe33229f2a65517.js",
    "/_next/static/chunks/2619-04bc32f026a0d946.js",
    "/_next/static/chunks/3305-79dd8a8fc1e38ada.js",
    "/_next/static/chunks/3893-d9498988816ad22b.js",
    "/_next/static/chunks/4909-64796d901b595af7.js",
    "/_next/static/chunks/4bd1b696-100b9d70ed4e49c1.js",
    "/_next/static/chunks/6161-d28a6591ea9c6b4b.js",
    "/_next/static/chunks/7267-1959fdcb8c860427.js",
    "/_next/static/chunks/app/(site)/about/page-5c3eb29d251a205e.js",
    "/_next/static/chunks/app/(site)/contact/page-3003cf61d17cdec3.js",
    "/_next/static/chunks/app/(site)/layout-114056d30e0e7332.js",
    "/_next/static/chunks/app/(site)/page-49b8b31183b97ce0.js",
    "/_next/static/chunks/app/(site)/work/%5Bslug%5D/page-d59fc2a7d0698fb2.js",
    "/_next/static/chunks/app/(site)/work/page-681802aca63f1a1c.js",
    "/_next/static/chunks/app/error-ca1d986e379c1fda.js",
    "/_next/static/chunks/app/layout-d8ee6cb66670c2bc.js",
    "/_next/static/chunks/app/not-found-d6d272be134901b8.js",
    "/_next/static/chunks/main-app-b7ac91ae224968d9.js",
    "/_next/static/chunks/polyfills-42372ed130431b0a.js",
    "/_next/static/chunks/webpack-28a343742f334580.js"
]

for k in known_files:
    all_assets.add(clean_rel_path(k))

# 4. Download all assets
cleaned_assets = set()
for a in all_assets:
    c = clean_rel_path(a)
    if c and c not in PAGES and not c.endswith("/") and not c.endswith(".html") and not c.endswith(".rsc"):
        cleaned_assets.add(c)

print(f"Downloading {len(cleaned_assets)} regular assets...")
for ast in sorted(cleaned_assets):
    parsed = urllib.parse.urlsplit(ast)
    quoted_path = urllib.parse.quote(urllib.parse.unquote(parsed.path))
    target_url = BASE_URL + quoted_path
    print(f"Downloading asset: {ast}")
    data = fetch_url(target_url, as_bytes=True)
    if data:
        save_file(ast, data)
        # If it's a CSS file, parse for url(...)
        if ast.endswith(".css"):
            css_text = data.decode("utf-8", errors="ignore")
            css_urls = re.findall(r'url\([\'"]?([^\'"\)\#]+)[\'"]?\)', css_text)
            for cu in css_urls:
                cu_clean = clean_rel_path(cu)
                if cu_clean and not cu_clean.startswith("data:"):
                    if not cu_clean.startswith("/"):
                        cu_clean = "/_next/static/css/" + cu_clean
                    print(f"Discovered in CSS: {cu_clean}")
                    cdata = fetch_url(BASE_URL + urllib.parse.quote(urllib.parse.unquote(cu_clean)), as_bytes=True)
                    if cdata:
                        save_file(cu_clean, cdata)

# 5. Download next/image optimized images
print(f"Downloading {len(all_next_images)} Next.js optimized images...")
image_cache_map = {}
for n_img in sorted(all_next_images):
    target_url = BASE_URL + n_img
    print(f"Downloading Next image: {n_img[:70]}...")
    data = fetch_url(target_url, as_bytes=True)
    if data:
        qs = urllib.parse.parse_qs(urllib.parse.urlsplit(n_img).query)
        orig_url = qs.get("url", [None])[0]
        if orig_url:
            orig_clean = clean_rel_path(orig_url)
            orig_data = fetch_url(BASE_URL + urllib.parse.quote(urllib.parse.unquote(orig_clean)), as_bytes=True)
            if orig_data:
                save_file(orig_clean, orig_data)

        # Hash filename for cache
        h = hashlib.sha256(n_img.encode("utf-8")).hexdigest()[:16]
        ext = ".webp" if b"WEBP" in data[:12] or b"RIFF" in data[:4] else ".png"
        cache_rel = f"_next_image_cache/{h}{ext}"
        cache_path = os.path.join(DEST_DIR, cache_rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, "wb") as f:
            f.write(data)
        image_cache_map[n_img] = cache_rel

with open(os.path.join(DEST_DIR, "next_image_map.json"), "w", encoding="utf-8") as f:
    json.dump(image_cache_map, f, indent=2)

print("SUCCESS: Done downloading all assets!")
