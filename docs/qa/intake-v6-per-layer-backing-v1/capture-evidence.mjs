/**
 * Runtime evidence — per-layer Forex backing (Slice B)
 */
import { chromium } from "@playwright/test";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT_DIR = path.join(__dirname, "screenshots");
const WORKSPACE = "b00a3a0c-5a3d-4d0b-a95e-582bb542dde1";
const ROUTE = `http://127.0.0.1:3000/intake-v6/${WORKSPACE}/operator`;

async function gotoReviewFinisaje(page) {
  await page.getByTestId("intake-v6-progress-step-review").click({ timeout: 60_000 });
  await page.getByTestId("intake-v6-step-review").waitFor({ timeout: 60_000 });
  await page.getByTestId("intake-v6-review-tab-finisaje").click().catch(() => {});
  await page.waitForTimeout(1500);
}

async function main() {
  await mkdir(OUT_DIR, { recursive: true });
  const report = { workspace: WORKSPACE, route: ROUTE, backingSelectors: 0, globalSelector: false };

  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1200 } });
  await page.goto(ROUTE, { waitUntil: "domcontentloaded", timeout: 120_000 });
  await page.waitForTimeout(2000);
  await gotoReviewFinisaje(page);

  report.globalSelector = (await page.getByTestId("intake-v6-review-backing-finish-integration").count()) > 0;
  const backingSelects = page.locator('[data-testid^="intake-v6-backing-mode-"]');
  report.backingSelectors = await backingSelects.count();

  if (report.backingSelectors >= 2) {
    await backingSelects.nth(0).selectOption("forex_10_no_bevel");
    await backingSelects.nth(1).selectOption("forex_10_with_bevel");
    await page.waitForTimeout(2500);
  }

  await page.screenshot({ path: path.join(OUT_DIR, "01_per_layer_backing_review.png"), fullPage: true });
  await page.reload({ waitUntil: "domcontentloaded" });
  await gotoReviewFinisaje(page);
  await page.waitForTimeout(1500);
  await page.screenshot({ path: path.join(OUT_DIR, "02_reload_persisted_backing.png"), fullPage: true });

  await writeFile(path.join(__dirname, "evidence_report.json"), JSON.stringify(report, null, 2));
  await browser.close();
  console.log(JSON.stringify(report, null, 2));
}

main().catch(async (err) => {
  console.error(err);
  process.exit(1);
});
