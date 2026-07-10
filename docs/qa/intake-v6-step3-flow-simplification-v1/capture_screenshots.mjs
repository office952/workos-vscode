/**
 * Capture Step 3 flow simplification screenshots (read-only UI navigation).
 *
 * Prerequisites: backend :8000, frontend :3000, workspace 22ef834d-f2d0-453b-a7a7-118928c98a39
 *
 * Usage:
 *   cd frontend
 *   node ../docs/qa/intake-v6-step3-flow-simplification-v1/capture_screenshots.mjs
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

async function main() {
  await mkdir(OUT, { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto(BASE, { waitUntil: "networkidle" });

  await shot(page, "01_step2_configuration_main.png");

  await page.getByTestId("intake-v6-progress-step-review").click();
  await page.waitForTimeout(800);
  await shot(page, "02_step2_real_blocker_visible.png");

  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await shot(page, "03_final_summary_collapsed.png");

  await page.getByTestId("intake-v6-final-configuration-summary-toggle").click();
  await page.waitForTimeout(400);
  await shot(page, "04_final_summary_expanded.png");

  await page.getByTestId("intake-v6-final-configuration-technical-details-toggle").click();
  await shot(page, "05_technical_details_collapsed.png");

  await page.getByTestId("intake-v6-final-configuration-technical-details-toggle").click();
  await page.waitForTimeout(300);
  await shot(page, "06_technical_details_expanded.png");

  await shot(page, "07_final_action_ready_state.png");
  await shot(page, "08_final_action_blocked_state.png");

  await browser.close();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
