import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';

const urls = fs.readFileSync('cali_batch6_selected_urls.txt', 'utf8')
  .split(/\r?\n/).map(x => x.trim()).filter(Boolean);
const outDir = path.resolve('cali-batch6-actual');
const screenshotsDir = path.join(outDir, 'screenshots');
fs.mkdirSync(screenshotsDir, { recursive: true });

const devices = [
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
    ['rental-income-roi-claim', ['rental income', 'return on investment', 'roi', 'pay for itself', 'makes you more money']],
    ['best-contractor-claim', ['best contractor', 'top-rated', 'top rated', 'trusted contractor']],
    ['rating-review-claim', ['google rating', 'star rating', '5-star', 'five-star', 'reviews']],
    ['financing-claim', ['financing available', 'financing options', 'payment plans']],
    ['warranty-claim', ['year warranty', 'years warranty', 'lifetime warranty']],
    ['public-address-claim', ['2802 paseo del sol']],
    ['placeholder-residue', ['write your caption here', 'slide title', 'lorem ipsum', 'this is a subtitle for your new post']],
    ['stale-year', ['2024', '2025', '2026']],
  ];
  return rules.filter(([, terms]) => terms.some(term => low.includes(term))).map(([name]) => name);
}

async function captureOne(browser, url, device, options) {
  const context = await browser.newContext({
    ...options,
    locale: 'en-US',
    colorScheme: 'light',
    reducedMotion: 'reduce',
    ignoreHTTPSErrors: true,
  });
  const page = await context.newPage();
  page.setDefaultTimeout(60000);
  const consoleErrors = [];
  const requestFailures = [];
  page.on('console', msg => { if (msg.type() === 'error') consoleErrors.push(msg.text().slice(0, 1000)); });
  page.on('pageerror', err => consoleErrors.push(String(err).slice(0, 1000)));
  page.on('requestfailed', req => requestFailures.push({ url: req.url(), error: req.failure()?.errorText || '' }));
  const id = slug(url);
  const result = { requestedUrl: url, device, slug: id, error: '' };
  try {
    const response = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 90000 });
    await page.waitForTimeout(1500);
    await page.evaluate(async () => {
      const max = Math.max(document.body?.scrollHeight || 0, document.documentElement.scrollHeight);
      for (let y = 0; y < max; y += 900) {
        window.scrollTo(0, y);
        await new Promise(resolve => setTimeout(resolve, 45));
      }
      window.scrollTo(0, 0);
    });
    await page.waitForTimeout(700);
    result.status = response?.status() ?? null;
    Object.assign(result, await page.evaluate(() => {
      const body = (document.body?.innerText || '').replace(/\s+/g, ' ').trim();
      const h1s = [...document.querySelectorAll('h1')].map(el => el.innerText.trim()).filter(Boolean);
      return {
        finalUrl: location.href,
        title: document.title,
        h1: h1s[0] || '',
        h1Count: h1s.length,
        canonical: document.querySelector('link[rel="canonical"]')?.href || '',
        robots: document.querySelector('meta[name="robots"]')?.content || '',
        metaDescription: document.querySelector('meta[name="description"]')?.content || '',
        wordCount: body ? body.split(/\s+/).length : 0,
        textExcerpt: body.slice(0, 12000),
        viewportWidth: innerWidth,
        scrollWidth: Math.max(document.documentElement.scrollWidth, document.body?.scrollWidth || 0),
        scrollHeight: Math.max(document.documentElement.scrollHeight, document.body?.scrollHeight || 0),
        reviewMarkers: [...document.querySelectorAll('[data-cali-widget],[data-cali-edge-component]')]
          .map(el => el.getAttribute('data-cali-widget') || el.getAttribute('data-cali-edge-component')).filter(Boolean),
        formCount: document.querySelectorAll('form, iframe[src*="form"], iframe[src*="leadconnectorhq"]').length,
        links: [...document.querySelectorAll('a[href]')].slice(0, 100)
          .map(a => ({ text: (a.innerText || '').trim().slice(0, 120), href: a.href })),
      };
    }));
    result.flags = detectFlags(result.textExcerpt || '', result.title || '', result.h1 || '');
    result.horizontalOverflowPx = Math.max(0, (result.scrollWidth || 0) - (result.viewportWidth || 0));
    result.consoleErrors = consoleErrors.slice(0, 25);
    result.requestFailures = requestFailures.slice(0, 25);
    await page.screenshot({ path: path.join(screenshotsDir, `${id}__${device}__top.png`), fullPage: false });
    await page.screenshot({ path: path.join(screenshotsDir, `${id}__${device}__full.jpg`), fullPage: true, type: 'jpeg', quality: 52 });
  } catch (error) {
    result.error = String(error?.stack || error);
    try { await page.screenshot({ path: path.join(screenshotsDir, `${id}__${device}__error.png`), fullPage: false }); } catch {}
  }
  await context.close();
  return result;
}

async function pool(items, concurrency, task) {
  const results = new Array(items.length);
  let next = 0;
  await Promise.all(Array.from({ length: Math.min(concurrency, items.length) }, async () => {
    while (true) {
      const index = next++;
      if (index >= items.length) return;
      results[index] = await task(items[index], index);
    }
  }));
  return results;
}

const browser = await chromium.launch({ headless: true });
const manifest = [];
for (const [device, options] of devices) {
  manifest.push(...await pool(urls, 4, url => captureOne(browser, url, device, options)));
}
await browser.close();

fs.writeFileSync(path.join(outDir, 'capture_manifest.json'), JSON.stringify(manifest, null, 2));
fs.writeFileSync(path.join(outDir, 'selected_urls.txt'), urls.join('\n') + '\n');
fs.writeFileSync(path.join(outDir, 'coverage_summary.json'), JSON.stringify({
  capturedUniquePages: urls.length,
  screenshotFiles: fs.readdirSync(screenshotsDir).length,
  successfulCaptures: manifest.filter(item => !item.error).length,
  navigationErrors: manifest.filter(item => item.error).length,
  mobileOverflowPages: manifest.filter(item => item.device === 'mobile' && item.horizontalOverflowPx > 0).length,
  consoleErrorPages: manifest.filter(item => item.consoleErrors?.length).length,
  requestFailurePages: manifest.filter(item => item.requestFailures?.length).length,
}, null, 2));