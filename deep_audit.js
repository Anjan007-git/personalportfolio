const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');
const path = require('path');

const LIVE_BASE = 'https://tanishbhavsar.vercel.app';
const LOCAL_BASE = 'http://localhost:3000';

const ROUTES = [
  '/',
  '/about',
  '/work',
  '/contact',
  '/work/credzen',
  '/work/mediq',
  '/work/rapid-crisis-response',
  '/work/ajinkya-jadhav-photography'
];

const VIEWPORTS = [
  { name: 'desktop', width: 1440, height: 900 },
  { name: 'tablet', width: 768, height: 1024 },
  { name: 'mobile', width: 375, height: 812 }
];

async function launchChrome(port) {
  const chromePath = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
  const chrome = spawn(chromePath, [
    '--headless=new',
    `--remote-debugging-port=${port}`,
    '--disable-gpu',
    '--no-first-run',
    'about:blank'
  ]);
  await new Promise(r => setTimeout(r, 1500));
  return chrome;
}

async function connectCDP(port) {
  const targets = await new Promise((resolve, reject) => {
    http.get(`http://127.0.0.1:${port}/json`, res => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve(JSON.parse(data)));
    }).on('error', reject);
  });
  const page = targets.find(t => t.type === 'page') || targets[0];
  const ws = new WebSocket(page.webSocketDebuggerUrl);

  let msgId = 1;
  const callbacks = new Map();
  const failedRequests = [];
  const allRequests = [];
  const consoleErrors = [];

  function send(method, params = {}) {
    return new Promise((resolve, reject) => {
      const id = msgId++;
      callbacks.set(id, { resolve, reject });
      ws.send(JSON.stringify({ id, method, params }));
    });
  }

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    if (msg.id && callbacks.has(msg.id)) {
      callbacks.get(msg.id).resolve(msg.result);
      callbacks.delete(msg.id);
    }
    if (msg.method === 'Network.responseReceived') {
      const { response } = msg.params;
      allRequests.push({ url: response.url, status: response.status, mime: response.mimeType });
      if (response.status >= 400) {
        failedRequests.push({ url: response.url, status: response.status });
      }
    }
    if (msg.method === 'Runtime.consoleAPICalled') {
      if (msg.params.type === 'error') {
        consoleErrors.push(msg.params.args.map(a => a.value || a.description).join(' '));
      }
    }
    if (msg.method === 'Runtime.exceptionThrown') {
      consoleErrors.push(msg.params.exceptionDetails.text + ' ' + (msg.params.exceptionDetails.exception?.description || ''));
    }
  };

  await new Promise(r => ws.onopen = r);
  await send('Network.enable');
  await send('Page.enable');
  await send('Runtime.enable');
  await send('DOM.enable');

  return { send, ws, failedRequests, allRequests, consoleErrors };
}

async function inspectPage(cdp, url, viewport, screenshotPath) {
  cdp.failedRequests.length = 0;
  cdp.allRequests.length = 0;
  cdp.consoleErrors.length = 0;

  // Set viewport
  await cdp.send('Emulation.setDeviceMetricsOverride', {
    width: viewport.width,
    height: viewport.height,
    deviceScaleFactor: 1,
    mobile: viewport.name === 'mobile'
  });

  await cdp.send('Page.navigate', { url });
  // Wait for network idle and animations
  await new Promise(r => setTimeout(r, 3500));

  // Extract page metadata & DOM details
  const evalResult = await cdp.send('Runtime.evaluate', {
    expression: `(() => {
      const buttons = Array.from(document.querySelectorAll('button')).map(b => ({
        text: b.innerText.trim(),
        ariaLabel: b.getAttribute('aria-label'),
        classes: b.className
      }));
      const links = Array.from(document.querySelectorAll('a')).map(a => ({
        href: a.getAttribute('href'),
        text: a.innerText.trim()
      }));
      const forms = Array.from(document.querySelectorAll('form')).map(f => ({
        action: f.getAttribute('action'),
        method: f.getAttribute('method'),
        inputs: Array.from(f.querySelectorAll('input, textarea, select')).map(i => ({
          name: i.name,
          type: i.type,
          placeholder: i.placeholder,
          required: i.required
        }))
      }));
      const headings = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6')).map(h => ({
        tag: h.tagName,
        text: h.innerText.trim()
      }));
      const audios = Array.from(document.querySelectorAll('audio')).map(a => a.src);
      const videos = Array.from(document.querySelectorAll('video')).map(v => v.src);
      const canvases = document.querySelectorAll('canvas').length;

      return {
        title: document.title,
        buttonsCount: buttons.length,
        buttons: buttons.slice(0, 15),
        linksCount: links.length,
        links: links.slice(0, 20),
        forms,
        headings,
        audios,
        videos,
        canvases,
        scrollHeight: document.body.scrollHeight,
        htmlLength: document.documentElement.outerHTML.length
      };
    })()`,
    returnByValue: true
  });

  // Capture screenshot
  let screenshot = null;
  if (screenshotPath) {
    const shotData = await cdp.send('Page.captureScreenshot', { format: 'png' });
    fs.writeFileSync(screenshotPath, Buffer.from(shotData.data, 'base64'));
    screenshot = screenshotPath;
  }

  return {
    url,
    viewport: viewport.name,
    data: evalResult.result.value,
    failedRequests: [...cdp.failedRequests],
    allRequestsCount: cdp.allRequests.length,
    consoleErrors: [...cdp.consoleErrors],
    screenshot
  };
}

async function main() {
  console.log('--- STARTING DEEP AUDIT: LIVE vs CLONE ---');
  const chrome = await launchChrome(9222);
  const cdp = await connectCDP(9222);

  const auditDir = path.join(__dirname, 'audit_results');
  if (!fs.existsSync(auditDir)) fs.mkdirSync(auditDir);

  const report = [];

  for (const r of ROUTES) {
    console.log(`\n========================================`);
    console.log(`Auditing route: ${r}`);
    console.log(`========================================`);

    for (const vp of VIEWPORTS) {
      console.log(`  Viewport: ${vp.name} (${vp.width}x${vp.height})`);

      const liveUrl = `${LIVE_BASE}${r}`;
      const localUrl = `${LOCAL_BASE}${r}`;

      const liveShot = path.join(auditDir, `live_${r.replace(/\//g, '_')}_${vp.name}.png`);
      const localShot = path.join(auditDir, `local_${r.replace(/\//g, '_')}_${vp.name}.png`);

      const liveData = await inspectPage(cdp, liveUrl, vp, liveShot);
      const localData = await inspectPage(cdp, localUrl, vp, localShot);

      const comparison = {
        route: r,
        viewport: vp.name,
        live: {
          title: liveData.data.title,
          headingsCount: liveData.data.headings.length,
          buttonsCount: liveData.data.buttonsCount,
          linksCount: liveData.data.linksCount,
          formsCount: liveData.data.forms.length,
          canvases: liveData.data.canvases,
          failedRequests: liveData.failedRequests.length,
          consoleErrors: liveData.consoleErrors.length,
          scrollHeight: liveData.data.scrollHeight,
          forms: liveData.data.forms
        },
        local: {
          title: localData.data.title,
          headingsCount: localData.data.headings.length,
          buttonsCount: localData.data.buttonsCount,
          linksCount: localData.data.linksCount,
          formsCount: localData.data.forms.length,
          canvases: localData.data.canvases,
          failedRequests: localData.failedRequests.length,
          consoleErrors: localData.consoleErrors.length,
          scrollHeight: localData.data.scrollHeight,
          forms: localData.data.forms
        },
        liveErrors: liveData.consoleErrors,
        localErrors: localData.consoleErrors,
        localFailedReqs: localData.failedRequests
      };

      console.log(`    Live  -> Headings: ${comparison.live.headingsCount}, Buttons: ${comparison.live.buttonsCount}, Links: ${comparison.live.linksCount}, ScrollHeight: ${comparison.live.scrollHeight}, FailedReqs: ${comparison.live.failedRequests}`);
      console.log(`    Local -> Headings: ${comparison.local.headingsCount}, Buttons: ${comparison.local.buttonsCount}, Links: ${comparison.local.linksCount}, ScrollHeight: ${comparison.local.scrollHeight}, FailedReqs: ${comparison.local.failedRequests}`);

      if (comparison.localFailedReqs.length > 0) {
        console.warn(`    ⚠️ Local Failed Requests:`, comparison.localFailedReqs);
      }
      if (comparison.localErrors.length > 0) {
        console.warn(`    ⚠️ Local Console Errors:`, comparison.localErrors);
      }

      report.push(comparison);
    }
  }

  fs.writeFileSync(path.join(auditDir, 'audit_report.json'), JSON.stringify(report, null, 2));
  console.log(`\nAudit complete! Report saved to audit_results/audit_report.json`);

  cdp.ws.close();
  chrome.kill();
  process.exit(0);
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});

