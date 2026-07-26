/**
 * Slice 1 screenshot capture — Intake V6 Step 2 blocker banner.
 */
import { chromium } from "playwright";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.join(__dirname, "screenshots");
fs.mkdirSync(OUT, { recursive: true });

const URL =
  "http://127.0.0.1:3000/intake-v6/22ef834d-f2d0-453b-a7a7-118928c98a39/operator";

async function shot(page, name) {
  await page.screenshot({ path: path.join(OUT, `${name}.png`), fullPage: true });
  console.log("saved", name);
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto(URL, { waitUntil: "networkidle", timeout: 120_000 });
  await page.waitForTimeout(3000);

  await page.getByTestId("intake-v6-progress-step-review").click();
  await page.waitForTimeout(2000);
  await page.getByTestId("intake-v6-review-tab-finisaje").click();
  await page.waitForTimeout(1000);
  await page.evaluate(() => window.scrollTo(0, 0));
  await shot(page, "01_step2_finisaje_banner_visible");

  await page.evaluate(() => window.scrollTo(0, 0));
  await shot(page, "02_step2_diagnostic_collapsed_with_banner");

  const backboneToggle = page.getByTestId("form-system-backbone-toggle");
  if ((await backboneToggle.count()) > 0) {
    await backboneToggle.click();
    await page.waitForTimeout(600);
  }
  const techToggle = page.getByTestId("intake-v6-review-technical-details-toggle");
  if ((await techToggle.count()) > 0) {
    const expanded = await page.getByTestId("intake-v6-review-technical-details").getAttribute("data-expanded");
    if (expanded !== "true") await techToggle.click();
    await page.waitForTimeout(600);
  }
  await diagnosticRefScroll(page);
  await shot(page, "03_step2_diagnostic_expanded_raw_codes");

  await page.getByTestId("intake-v6-progress-step-confirm").click();
  await page.waitForTimeout(2000);
  await page.evaluate(() => window.scrollTo(0, 0));
  await shot(page, "04_step3_no_regression");

  await browser.close();
}

async function diagnosticRefScroll(page) {
  await page.locator("#intake-v6-review-diagnostic-tehnic").scrollIntoViewIfNeeded();
  await page.waitForTimeout(400);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
