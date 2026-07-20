const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const OUT = path.join(process.cwd(), 'cali-batch7-actual');
fs.mkdirSync(path.join(OUT, 'screenshots'), { recursive: true });
const URLS = fs.readFileSync(path.join(ROOT, 'batch7', 'selected_urls.txt'), 'utf8')
  .split(/\r?\n/).map(x => x.trim()).filter(Boolean);

const DEVICES = [
  ['desktop', { viewport: { width: 1440, height: 1000 }, isMobile: false, hasTouch: false }],
  ['mobile', { viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true }],
];

function slug(url) {
  return (new URL(url).pathname.replace(/^\/+|\/+$/g, '') || 'home')
    .replace(/[^a-z0-9]+/gi, '-').replace(/^-|-$/g, '').toLowerCase().slice(0, 110);
}

function detectFlags(text, title, h1) {
  const low = `${title} ${h1} ${text}`.toLowerCase();
  const rules = [
    ['design-build-language', ['design-build', 'design build']],
    ['in-house-design-claim', ['our designers', 'our architects', 'in-house designer', 'in-house architect']],
    ['free-estimate-claim', ['free estimate', 'free consultation', 'free in-home assessment']],
    ['fixed-price-claim', ['price range', '$10,000', '$15,000', '$20,000', '$25,000', '$30,000', '$50,000', '$100,000', 'per square foot']],
    ['fixed-timeline-claim', ['weeks to complete', 'completed in', 'project timeline', 'week-by-week']],
    ['rental-income-roi-claim', ['rental income', 'return on investment', ' roi ', 'pay for itself', 'makes you more money']],
    ['best-contractor-claim', ['best contractor', 'top-rated', 'top rated', 'trusted contractor', 'best choice']],
    ['rating-review-claim', ['google rating', 'star rating', '5-star', 'five-star', ' reviews']],
    ['financing-claim', ['financing available', 'financing options', 'payment plans']],
    ['warranty-claim', ['year warranty', 'years warranty', 'lifetime warranty']],
    ['public-address-claim', ['2802 paseo del sol']],
    ['placeholder-residue', ['write your caption here', 'slide title', 'lorem ipsum', 'this is a subtitle for your new post']],
    ['stale-year', ['2024', '2025', '2026']],
  ];
  return rules.filter(([_, terms]) => terms.some(t => low.includes(t))).map(([name]) => name);
}

async function captureOne(browser, url, device, opts) {
  const context = await browser.newContext({ ...opts, locale: 'en-US', colorScheme: 'light', reducedMotion: 'reduce', ignoreHTTPSErrors: true });
  const page = await context.newPage();
  page.setDefaultTimeout(60000);
  const consoleErrors = [];
  const requestFailures = [];
  page.on('console', msg => { if (msg.type() === 'error') consoleErrors.push(msg.text().slice(0, 1000)); });
  page.on('pageerror', err => consoleErrors.push(String(err).slice(0, 1000)));
  page.on('requestfailed', req => requestFailures.push({ url: req.url(), error: req.failure()?.errorText || '' }));
  const s = slug(url);
  const out = { requestedUrl: url, device, slug: s, error: '' };
  try {
    const response = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 90000 });
    await page.waitForTimeout(1500);
    await page.evaluate(async () => {
      const max = Math.max(document.body?.scrollHeight || 0, document.documentElement.scrollHeight);
      for (let y = 0; y < max; y += 900) {
        window.scrollTo(0, y);
        await new Promise(r => setTimeout(r, 45));
      }
      window.scrollTo(0, 0);
    });
    await page.waitForTimeout(700);
    out.status = response ? response.status() : null;
    Object.assign(out, await page.evaluate(() => {
      const body = (document.body?.innerText || '').replace(/\s+/g, ' ').trim();
      const h1s = [...document.querySelectorAll('h1')].map(e => e.innerText.trim()).filter(Boolean);
      return {
        finalUrl: location.href,
        title: document.title,
        h1: h1s[0] || '',
        h1Count: h1s.length,
        canonical: document.querySelector('link[rel="canonical"]')?.href || '',
        robots: document.querySelector('meta[name="robots"]')?.content || '',
        metaDescription: document.querySelector('meta[name="description"]')?.content || '',
        wordCount: body ? body.split(/\s+/).length : 0,
        textExcerpt: body.slice(0, 14000),
        viewportWidth: innerWidth,
        scrollWidth: Math.max(document.documentElement.scrollWidth, document.body?.scrollWidth || 0),
        scrollHeight: Math.max(document.documentElement.scrollHeight, document.body?.scrollHeight || 0),
        reviewMarkers: [...document.querySelectorAll('[data-cali-widget],[data-cali-edge-component]')]
          .map(e => e.getAttribute('data-cali-widget') || e.getAttribute('data-cali-edge-component')).filter(Boolean),
        formCount: document.querySelectorAll('form, iframe[src*="form"], iframe[src*="leadconnectorhq"]').length,
        links: [...document.querySelectorAll('a[href]')].slice(0, 120).map(a => ({ text: (a.innerText || '').trim().slice(0, 120), href: a.href })),
      };
    }));
    out.flags = detectFlags(out.textExcerpt || '', out.title || '', out.h1 || '');
    out.horizontalOverflowPx = Math.max(0, (out.scrollWidth || 0) - (out.viewportWidth || 0));
    out.consoleErrors = consoleErrors.slice(0, 25);
    out.requestFailures = requestFailures.slice(0, 25);
    await page.screenshot({ path: path.join(OUT, 'screenshots', `${s}__${device}__top.png`), fullPage: false });
    await page.screenshot({ path: path.join(OUT, 'screenshots', `${s}__${device}__full.jpg`), fullPage: true, type: 'jpeg', quality: 52 });
  } catch (e) {
    out.error = String(e && e.stack ? e.stack : e);
    try { await page.screenshot({ path: path.join(OUT, 'screenshots', `${s}__${device}__error.png`), fullPage: false }); } catch (_) {}
  }
  await context.close();
  return out;
}

async function pool(items, limit, fn) {
  const results = new Array(items.length);
  let next = 0;
  await Promise.all(Array.from({ length: Math.min(limit, items.length) }, async () => {
    while (true) {
      const i = next++;
      if (i >= items.length) return;
      results[i] = await fn(items[i], i);
    }
  }));
  return results;
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const rows = [];
  for (const [device, opts] of DEVICES) {
    rows.push(...await pool(URLS, 4, url => captureOne(browser, url, device, opts)));
  }
  await browser.close();
  fs.writeFileSync(path.join(OUT, 'capture_manifest.json'), JSON.stringify(rows, null, 2));
  fs.writeFileSync(path.join(OUT, 'selected_urls.txt'), URLS.join('\n') + '\n');
  const summary = {
    capturedUniquePages: URLS.length,
    screenshotFiles: fs.readdirSync(path.join(OUT, 'screenshots')).length,
    successfulCaptures: rows.filter(x => !x.error).length,
    navigationErrors: rows.filter(x => x.error).length,
    httpStatusCounts: rows.reduce((a, x) => { a[x.status ?? 'error'] = (a[x.status ?? 'error'] || 0) + 1; return a; }, {}),
    pagesWithMobileOverflow: rows.filter(x => x.device === 'mobile' && x.horizontalOverflowPx > 0).map(x => x.requestedUrl),
    pagesWithReviewMarkers: [...new Set(rows.filter(x => x.reviewMarkers?.length).map(x => x.requestedUrl))],
    flagCounts: rows.filter(x => x.device === 'desktop').flatMap(x => x.flags || []).reduce((a, x) => { a[x] = (a[x] || 0) + 1; return a; }, {}),
  };
  fs.writeFileSync(path.join(OUT, 'coverage_summary.json'), JSON.stringify(summary, null, 2));
})().catch(err => { console.error(err); process.exit(1); });
