import urllib.request

test_urls = [
    'http://localhost:3000/',
    'http://localhost:3000/about',
    'http://localhost:3000/work',
    'http://localhost:3000/contact',
    'http://localhost:3000/work/credzen',
    'http://localhost:3000/_next/static/css/21f01898705a7723.css',
    'http://localhost:3000/_next/static/chunks/main-app-b7ac91ae224968d9.js',
    'http://localhost:3000/_next/static/chunks/app/(site)/work/%5Bslug%5D/page-d59fc2a7d0698fb2.js',
    'http://localhost:3000/_next/static/media/hero-portfolio.83853bb7.png',
    'http://localhost:3000/icons/Finder_Icon_macOS_Tahoe.png',
    'http://localhost:3000/_next/image?url=%2Fhands%2Fleft-hand.png&w=3840&q=75',
    'http://localhost:3000/desktop/wallpaper.webp'
]

all_passed = True
for u in test_urls:
    try:
        req = urllib.request.Request(u)
        with urllib.request.urlopen(req) as resp:
            ct = resp.headers.get('Content-Type')
            print(f'{u} -> {resp.status} ({ct}, {resp.length} bytes)')
    except Exception as e:
        print(f'{u} -> FAILED: {e}')
        all_passed = False

# Also test RSC header
try:
    rsc_req = urllib.request.Request('http://localhost:3000/about', headers={'RSC': '1'})
    with urllib.request.urlopen(rsc_req) as resp:
        ct = resp.headers.get('Content-Type')
        print(f'RSC Header: /about -> {resp.status} ({ct}, {resp.length} bytes)')
except Exception as e:
    print(f'RSC Header FAILED: {e}')
    all_passed = False

if all_passed:
    print('ALL TESTS PASSED PERFECTLY!')

