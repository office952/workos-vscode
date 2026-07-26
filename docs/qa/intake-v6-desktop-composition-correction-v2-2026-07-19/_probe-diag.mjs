import { createRequire } from "module";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(path.join(__dirname, "../../../frontend/package.json"));
const { chromium } = require("playwright");

const UI = "http://127.0.0.1:3000";
// use latest from failed capture if any — otherwise list workspaces via creating none
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });

const r = await fetch(`${UI}/api/v1/intake-v6/workspaces`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    title: `probe-diag-${Date.now()}`,
    selected_template_code: "TPL-VOLUMETRIC-LETTERS_v2",
    analyzer_mode: "analyzer_first",
  }),
});
const ws = await r.json();
await page.goto(`${UI}/intake-v6/${ws.id}/operator`, { waitUntil: "domcontentloaded", timeout: 120000 });
await page.waitForTimeout(1500);
await page.locator('[data-testid="intake-v6-progress-step-review"]').click({ force: true }).catch(() => null);
await page.waitForTimeout(2500);
const info = await page.evaluate(() => ({
  form: !!document.querySelector('[data-testid="intake-v6-review-form-region"]'),
  entry: !!document.querySelector('[data-testid="intake-v6-review-diagnostic-entry"]'),
  toggle: !!document.querySelector('[data-testid="intake-v6-review-technical-details-toggle"]'),
  accordion: document.querySelector('[data-testid="intake-v6-review-technical-details"]')?.getAttribute("data-expanded"),
  openText: document.body.innerText.includes("Deschide diagnostic tehnic"),
  analysisReady: !document.querySelector('[data-testid="intake-v6-review-blocked"]'),
}));
console.log(JSON.stringify(info, null, 2));
await browser.close();
