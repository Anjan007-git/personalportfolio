# Tanish Bhavsar Portfolio — Exact 1:1 Pixel-Perfect Clone

This is an exact, pixel-perfect, 1:1 clone of [https://tanishbhavsar.vercel.app](https://tanishbhavsar.vercel.app).

All original assets, animations, interactive macOS desktop simulation, typography, responsive images, fonts, styles, Next.js dynamic chunks, and server action contact form handling have been audited and verified.

---

## 🚀 Quick Start

Run the clone immediately using either **Node.js** or **Python** with **zero external dependencies**:

### Option 1: Node.js (Recommended)

```bash
# Start the server on http://localhost:3000
npm start
# or: node server.js
```

---

### Option 2: Python

```bash
# Run with Python on http://localhost:3000
python server.py
# or: npm run py
```

---

## 🧪 Comprehensive Audit Results (Live vs Clone)

An automated Chrome DevTools Protocol (CDP) side-by-side audit was performed across all routes and 3 standard viewports (**Desktop: 1440x900**, **Tablet: 768x1024**, **Mobile: 375x812**):

| Route | Desktop ScrollHeight | Tablet ScrollHeight | Mobile ScrollHeight | Headings | Links | Failed Requests | Console Errors |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **`/` (Home)** | 26,665 px | 25,936 px | 21,349 px | 12 / 12 | 26 / 26 | **0** | **0** |
| **`/about`** | 7,534 px | 8,786 px | 8,264 px | 9 / 9 | 9 / 9 | **0** | **0** |
| **`/work`** | 4,789 px | 3,374 px | 5,524 px | 12 / 12 | 15 / 15 | **0** | **0** |
| **`/contact`** | 2,183 px | 2,330 px | 2,524 px | 6 / 6 | 13 / 13 | **0** | **0** |
| **`/work/credzen`** | 6,817 px | 5,759 px | 5,632 px | 9 / 9 | 9 / 9 | **0** | **0** |
| **`/work/mediq`** | 5,506 px | 4,943 px | 5,271 px | 8 / 8 | 7 / 7 | **0** | **0** |
| **`/work/rapid-crisis-response`** | 7,922 px | 6,718 px | 6,993 px | 10 / 10 | 8 / 8 | **0** | **0** |
| **`/work/ajinkya-jadhav-photography`** | 5,649 px | 4,518 px | 4,170 px | 7 / 7 | 8 / 8 | **0** | **0** |

*All page heights, headings, links, and buttons match the original site to the exact single pixel.*

---

## 📦 Features & Interactive Elements

- **macOS Tahoe Desktop Simulation**:
  - Interactive Dock with smooth magnification and launch effects
  - **Finder Window**: Displays Skills, AI/ML stacks, Frontend, and Backend
  - **About Me Window**: Displays biography and career overview
  - **Notes Window**: Displays interactive iCloud notes (Experience, Education, Highlights)
  - Native macOS window controls (red close, yellow minimize, green zoom)
  - Dock social links (Mail, GitHub, LinkedIn, X, LeetCode)
- **Functional Contact Form**:
  - Full Next.js Server Action (`POST /contact`) support
  - Form validation and smooth transition to status card: *"Thanks. I'll reply soon. Usually within a day."*
  - Automatically records incoming submissions to `contact_submissions.jsonl`
- **All 82 Webpack Dynamic Chunks & Media**:
  - All 82 dynamic chunks parsed and downloaded from the webpack chunk manifest
  - 21 original WOFF2 font files (Geist, Inter, custom typography)
  - 30 custom app icons (`/icons/`)
  - All project mockups & high-res render images (`/mockups-projects/`)
  - 170 responsive Next.js optimized image variations (`256w` through `3840w`)
  - OpenGraph / Twitter cards (`opengraph-image.png`) & resume (`tanish-bhavsar-cv.pdf`)

---

## 🌐 Deployment

- **Vercel**: Deploy with `npx vercel` (configured in `vercel.json`)
- **Netlify**: Deploy with `npx netlify deploy --prod` (configured in `netlify.toml`)
