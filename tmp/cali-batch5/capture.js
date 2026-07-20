const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const urls = fs.readFileSync(path.join(__dirname, 'urls.txt'), 'utf8').split(/\r?\n/).map(x => x.trim()).filter(Boolean);
const out = path.join(process.cwd(), 'cali-batch5-actual');
fs.mkdirSync(path.join(out, 'screenshots'), { recursive: true });
function slug(url) { return (new URL(url).pathname.replace(/^\/+|\/+$/g, '') || 'home').replace(/[^a-z0-9]+/gi, '-').toLowerCase().slice(0, 110); }
async function capture(browser, url, device, opts) {
  const ctx = await browser.newContext({ ...opts, ignoreHTTPSErrors: true, locale: 'en-US', reducedMotion: 'reduce' });
  const page = await ctx.newPage();
  const consoleErrors = [];
  const failedRequests = [];
  page.on('console', m => { if (m.type() === 'error') consoleErrors.push(m.text().slice(0, 500)); });
  page.on('requestfailed', r => failedRequests.push({ url: r.url(), error: r.failure()?.errorText || '' }));
  const s = slug(url);
  const result = { requestedUrl: url, device, slug: s, error: '' };
  try {
    const response = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 90000 });
    await page.waitForTimeout(1300);
    await page.evaluate(async () => {
      const max = Math.max(document.documentElement.scrollHeight, document.body?.scrollHeight || 0);
      for (let y = 0; y < max; y += 900) { scrollTo(0, y); await new Promise(r => setTimeout(r, 40)); }
      scrollTo(0, 0);
    });
    await page.waitForTimeout(600);
    result.status = response ? response.status() : null;
    Object.assign(result, await page.evaluate(() => {
      const text = (document.body?.innerText || '').replace(/\s+/g, ' ').trim();
      const h1s = [...document.querySelectorAll('h1')].map(e => e.innerText.trim()).filter(Boolean);
      return {
        finalUrl: location.href,
        title: document.title,
        h1: h1s[0] || '',
        h1Count: h1s.length,
        description: document.querySelector('meta[name="description"]')?.content || '',
        canonical: document.querySelector('link[rel="canonical"]')?.href || '',
        robots: document.querySelector('meta[name="robots"]')?.content || '',
        wordCount: text ? text.split(/\s+/).length : 0,
        textExcerpt: text.slice(0, 12000),
        viewportWidth: innerWidth,
        scrollWidth: Math.max(document.documentElement.scrollWidth, document.body?.scrollWidth || 0),
        reviewMarkers: [...document.querySelectorAll('[data-cali-widget],[data-cali-edge-component]')].map(e => e.getAttribute('data-cali-widget') || e.getAttribute('data-cali-edge-component')).filter(Boolean),
        formCount: document.querySelectorAll('form, iframe[src*="form"], iframe[src*="leadconnectorhq"]').length
      };
    }));
    result.horizontalOverflowPx = Math.max(0, result.scrollWidth - result.viewportWidth);
    result.consoleErrors = consoleErrors.slice(0, 20);
    result.failedRequests = failedRequests.slice(0, 20);
    await page.screenshot({ path: path.join(out, 'screenshots', `${s}__${device}__top.png`), fullPage: false });
    await page.screenshot({ path: path.join(out, 'screenshots', `${s}__${device}__full.jpg`), fullPage: true, type: 'jpeg', quality: 54 });
  } catch (e) {
    result.error = String(e);
  }
  await ctx.close();
  return result;
}
async function pool(items, count, fn) {
  const results = new Array(items.length); let next = 0;
  await Promise.all(Array.from({ length: count }, async () => {
    while (true) { const i = next++; if (i >= items.length) return; results[i] = await fn(items[i]); }
  }));
  return results;
}
(async () => {
  const browser = await chromium.launch({ headless: true });
  const all = [];
  for (const [device, opts] of [
    ['desktop', { viewport: { width: 1440, height: 1000 }, isMobile: false }],
    ['mobile', { viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true }]
  ]) all.push(...await pool(urls, 4, u => capture(browser, u, device, opts)));
  await browser.close();
  fs.writeFileSync(path.join(out, 'capture_manifest.json'), JSON.stringify(all, null, 2));
  fs.writeFileSync(path.join(out, 'selected_urls.txt'), urls.join('\n') + '\n');
  fs.writeFileSync(path.join(out, 'coverage_summary.json'), JSON.stringify({
    capturedUniquePages: urls.length,
    screenshotFiles: fs.readdirSync(path.join(out, 'screenshots')).length,
    successfulCaptures: all.filter(x => !x.error).length,
    navigationErrors: all.filter(x => x.error).length,
    statuses: all.reduce((a, x) => { const k = String(x.status ?? 'error'); a[k] = (a[k] || 0) + 1; return a; }, {})
  }, null, 2));
})().catch(e => { console.error(e); process.exit(1); });
