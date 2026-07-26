import { createRequire } from "module";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(path.join(__dirname, "../../../frontend/package.json"));
const { chromium } = require("playwright");

const UI = "http://127.0.0.1:3000";
const id = "939f7dc3-acca-40a9-a8aa-088ac31e6cbb";

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
await page.goto(`${UI}/intake-v6/${id}/operator`, { waitUntil: "domcontentloaded", timeout: 120000 });
await page.waitForTimeout(2000);
await page.locator('[data-testid="intake-v6-progress-step-review"]').click({ force: true }).catch(() => null);
await page.waitForTimeout(2500);

const tabs = await page.evaluate(() =>
  Array.from(document.querySelectorAll("[data-testid^='intake-v6-review-tab']")).map((el) => ({
    id: el.getAttribute("data-testid"),
    text: (el.textContent || "").trim().slice(0, 60),
    tag: el.tagName,
  })),
);
console.log("tabs", JSON.stringify(tabs, null, 2));

for (const tabId of [
  "intake-v6-review-tab-iluminare",
  "intake-v6-review-tab-montaj",
  "intake-v6-review-tab-finisaje",
]) {
  const loc = page.locator(`[data-testid="${tabId}"]`);
  console.log(tabId, "count", await loc.count());
  if ((await loc.count()) > 0) {
    await loc.click({ force: true });
    await page.waitForTimeout(1200);
    const state = await page.evaluate(() => ({
      fin: !!document.querySelector('[data-testid="intake-v6-review-tab-panel-finisaje"]'),
      ilum: !!document.querySelector('[data-testid="intake-v6-review-tab-panel-iluminare"]'),
      montaj: !!document.querySelector('[data-testid="intake-v6-review-tab-panel-montaj"]'),
      lighting: !!document.querySelector('[data-testid="intake-v6-review-lighting-section"]'),
      fundal: !!document.querySelector('[data-testid="intake-v6-fundal-carcasa-cluster"]'),
    }));
    console.log("after", tabId, state);
  }
}

await page.locator('[data-testid="intake-v6-confirm-product-composition"]').click({ force: true }).catch(() => null);
await page.waitForTimeout(2500);
await page.locator('[data-testid="intake-v6-progress-step-confirm"]').click({ force: true }).catch(() => null);
await page.waitForTimeout(1500);
await page.getByRole("button", { name: /Continuă la Confirmare/i }).first().click({ force: true }).catch(() => null);
await page.waitForTimeout(2500);
const confirm = await page.evaluate(() => ({
  href: location.href,
  firstPaint: !!document.querySelector('[data-testid="intake-v6-confirm-first-paint"]'),
  handoff: !!document.querySelector('[data-testid="intake-v6-quote-handoff"]'),
  step: !!document.querySelector('[data-testid="intake-v6-step-confirm"]'),
}));
console.log("confirm", confirm);

await browser.close();
