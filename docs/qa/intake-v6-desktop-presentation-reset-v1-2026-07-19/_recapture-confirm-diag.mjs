import fs from "fs";
import path from "path";
import { createRequire } from "module";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(path.join(__dirname, "../../../frontend/package.json"));
const { chromium } = require("playwright");

const UI = "http://127.0.0.1:3000";
const SHOTS = path.join(__dirname, "screenshots");
const id = "854fbb73-2329-4ee2-b9a0-21158f8eb1b9";

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });

await page.goto(`${UI}/intake-v6/${id}/operator`, { waitUntil: "domcontentloaded", timeout: 120000 });
await page.waitForTimeout(1500);
await page.locator('[data-testid="intake-v6-progress-step-review"]').click({ force: true }).catch(() => null);
await page.waitForSelector('[data-testid="intake-v6-review-tabs"]', { timeout: 30000 });
await page.waitForTimeout(1500);

// Diagnostic on montaj
await page.locator('[data-testid="intake-v6-review-tab-montaj"]').click({ force: true });
await page.waitForSelector('[data-testid="intake-v6-review-tab-panel-montaj"]');
await page.waitForTimeout(800);
await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
await page.waitForTimeout(500);

const diag = page.locator('[data-testid="intake-v6-review-technical-details"]');
console.log("diag count", await diag.count());
console.log(
  "diag attrs",
  await diag.evaluate((el) => ({
    expanded: el.getAttribute("data-expanded"),
    html: el.outerHTML.slice(0, 200),
  })).catch(() => null),
);
const toggle = page.locator('[data-testid="intake-v6-review-technical-details-toggle"]');
console.log("toggle count", await toggle.count());
if ((await toggle.count()) > 0) {
  const expanded = await diag.getAttribute("data-expanded");
  if (expanded === "true") await toggle.click({ force: true });
  await page.waitForTimeout(300);
  await page.screenshot({ path: path.join(SHOTS, "14_after_diagnostic_collapsed.png"), fullPage: false });
  await toggle.click({ force: true });
  await page.waitForTimeout(800);
  await page.locator('[data-testid="intake-v6-review-diagnostic-tehnic"]').scrollIntoViewIfNeeded().catch(() => null);
  await page.screenshot({ path: path.join(SHOTS, "15_after_diagnostic_expanded.png"), fullPage: false });
}

// Confirmare first paint (composition already confirmed on this workspace)
await page.locator('[data-testid="intake-v6-progress-step-confirm"]').click({ force: true }).catch(() => null);
await page.waitForTimeout(800);
await page.getByRole("button", { name: /Continuă la Confirmare/i }).first().click({ force: true }).catch(() => null);
await page.waitForSelector('[data-testid="intake-v6-confirm-first-paint"]', { timeout: 20000 });
await page.waitForTimeout(1500);
await page.screenshot({ path: path.join(SHOTS, "12_after_confirmare_ready.png"), fullPage: true });

const probe = await page.evaluate(() => {
  const handoff = document.querySelector('[data-testid="intake-v6-quote-handoff"]')?.textContent ?? "";
  const status = document.querySelector('[data-testid="intake-v6-final-config-status"]')?.textContent ?? "";
  return {
    firstPaint: !!document.querySelector('[data-testid="intake-v6-confirm-first-paint"]'),
    handoff,
    status,
    rawCodesInHandoff: /operator_confirmation_missing|product_truth_write|MOUNTING_SCOPE_INACTIVE/.test(handoff),
    rawCodesInStatus: /operator_confirmation_missing|product_truth_write/.test(status),
  };
});
console.log(JSON.stringify(probe, null, 2));
fs.writeFileSync(path.join(__dirname, "runtime/confirm_diag_recapture.json"), JSON.stringify(probe, null, 2));

await browser.close();
