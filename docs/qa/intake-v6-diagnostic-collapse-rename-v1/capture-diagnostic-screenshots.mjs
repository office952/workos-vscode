/**
 * Slice 3 screenshot capture — Intake V6 diagnostic collapse & rename.
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
  await shot(page, "01_step2_diagnostic_collapsed_default");

  await page.getByTestId("intake-v6-review-technical-details-toggle").click();
  await page.waitForTimeout(800);
  await page.locator("#intake-v6-review-diagnostic-tehnic").scrollIntoViewIfNeeded();
  await page.waitForTimeout(400);
  await shot(page, "02_step2_diagnostic_expanded_raw_codes");

  await page.getByTestId("intake-v6-review-technical-details-toggle").click();
  await page.waitForTimeout(500);
  await page.evaluate(() => window.scrollTo(0, 0));
  await shot(page, "03_step2_blocker_visible_diagnostic_collapsed");

  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await page.waitForTimeout(500);
  await shot(page, "04_step2_tab_badge_and_footer_relationship");

  await page.getByTestId("intake-v6-progress-step-layers").click();
  await page.waitForTimeout(2000);
  await page.evaluate(() => window.scrollTo(0, 0));
  await shot(page, "05_step1_no_badge_noise_regression");

  await page.getByTestId("intake-v6-progress-step-review").click();
  await page.waitForTimeout(1500);
  await page.getByTestId("intake-v6-review-tab-iluminare").click();
  await page.waitForTimeout(800);
  await page.evaluate(() => window.scrollTo(0, 0));
  await shot(page, "06_step2_iluminare_no_on_regression");

  await page.getByTestId("intake-v6-progress-step-confirm").click();
  await page.waitForTimeout(2000);
  await page.evaluate(() => window.scrollTo(0, 0));
  await shot(page, "07_step3_no_intentional_changes");

  await browser.close();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
