const { chromium } = require('playwright');
const path = require('path');
const outDir = process.argv[2];
const base = 'http://127.0.0.1:3000/product-system';
const tabs = [
  ['01-top-product-system-context.png', null],
  ['02-catalog-candidate-separation.png', null],
  ['03-candidate-overview.png', 'product-system-component-first-tab-overview'],
  ['04-components-tab.png', 'product-system-component-first-tab-components'],
  ['05-dossier-tab.png', 'product-system-component-first-tab-dossier'],
  ['06-form-system-tab.png', 'product-system-component-first-tab-form-system'],
  ['07-product-truth-tab.png', 'product-system-component-first-tab-product-truth'],
  ['08-guards-audit-tab.png', 'product-system-component-first-tab-guards-audit'],
  ['09-existing-roots-catalog.png', null],
];
(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto(base, { waitUntil: 'networkidle', timeout: 60000 });
  await page.waitForSelector('[data-testid="product-system-component-first-letters-set"]', { timeout: 30000 });
  for (const [file, tabId] of tabs) {
    if (tabId) await page.getByTestId(tabId).click();
    if (file.includes('existing-roots')) {
      await page.getByTestId('product-system-existing-roots').scrollIntoViewIfNeeded();
    } else if (file.includes('catalog-candidate')) {
      await page.getByTestId('product-system-candidate-sets').scrollIntoViewIfNeeded();
    } else if (file.includes('top-product')) {
      await page.evaluate(() => window.scrollTo(0, 0));
    }
    await page.waitForTimeout(400);
    await page.screenshot({ path: path.join(outDir, file), fullPage: false });
  }
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({ path: path.join(outDir, '10-full-candidate-area.png'), fullPage: true });
  await browser.close();
  console.log('Saved screenshots to', outDir);
})().catch((e) => { console.error(e); process.exit(1); });
