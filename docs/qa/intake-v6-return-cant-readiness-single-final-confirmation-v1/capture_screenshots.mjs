/**
 * Capture return/cant readiness + single final confirmation alignment screenshots.
 *
 * Prerequisites: backend :8000, frontend :3000, workspace 22ef834d-f2d0-453b-a7a7-118928c98a39
 *
 * Usage:
 *   cd frontend
 *   node ../docs/qa/intake-v6-return-cant-readiness-single-final-confirmation-v1/capture_screenshots.mjs
 */
import { chromium } from "playwright";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.join(__dirname, "screenshots");
const WORKSPACE_ID = "22ef834d-f2d0-453b-a7a7-118928c98a39";
const BASE = `http://127.0.0.1:3000/intake-v6/${WORKSPACE_ID}/operator`;

async function shot(page, name) {
  await page.screenshot({ path: path.join(OUT, name), fullPage: true });
  console.log("wrote", name);
}

async function gotoStep(page, stepId) {
  await page.getByTestId(`intake-v6-progress-step-${stepId}`).click();
  await page.waitForTimeout(900);
}

async function main() {
  await mkdir(OUT, { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto(BASE, { waitUntil: "networkidle" });

  await shot(page, "01_three_step_navigation.png");

  await gotoStep(page, "review");
  await page.evaluate(() => window.scrollTo(0, 0));
  await shot(page, "02_step2_cant_60mm_no_false_warning.png");

  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight / 2));
  await shot(page, "03_step2_print_laminate_no_false_warning.png");

  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await shot(page, "04_step2_real_blocker_only.png");

  await gotoStep(page, "confirm");
  await page.evaluate(() => window.scrollTo(0, 0));
  await shot(page, "05_step3_summary_collapsed.png");

  await page.getByTestId("intake-v6-final-configuration-summary-toggle").click();
  await page.waitForTimeout(500);
  await shot(page, "06_step3_summary_expanded.png");

  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await shot(page, "07_step3_final_confirmation.png");

  await page.getByTestId("intake-v6-final-configuration-summary-toggle").click();
  await page.waitForTimeout(300);
  await shot(page, "08_step3_blocked_real_missing_value.png");

  await page.getByTestId("intake-v6-final-configuration-summary-toggle").click();
  await page.waitForTimeout(300);
  await page.getByTestId("intake-v6-final-configuration-technical-details-toggle").click();
  await shot(page, "09_technical_details_collapsed.png");

  await page.getByTestId("intake-v6-final-configuration-technical-details-toggle").click();
  await page.waitForTimeout(400);
  await shot(page, "10_technical_details_expanded.png");

  await browser.close();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
