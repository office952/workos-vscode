/**
 * PRODUCT_SYSTEM_REFERENCE_COMPLETE — minimal closure screenshots.
 */
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import fs from "node:fs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.join(__dirname, "screenshots");
const BASE = process.env.FE_BASE || "http://127.0.0.1:3000";
const pwEntry = path.resolve(__dirname, "../../../frontend/node_modules/playwright/index.mjs");
const { chromium } = await import(pathToFileURL(pwEntry).href);

fs.mkdirSync(OUT, { recursive: true });
const shots = [];

async function shot(page, name, note) {
  const file = path.join(OUT, name);
  await page.screenshot({ path: file, fullPage: true });
  shots.push({ name, note, file });
  console.log("OK", name, note);
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1100 } });

  await page.goto(`${BASE}/product-system/products/TPL-VOLUMETRIC-LETTERS_v2`, {
    waitUntil: "networkidle",
    timeout: 60000,
  });
  await page.getByTestId("reference-complete-panel").waitFor({ timeout: 45000 });
  await page.getByTestId("reference-complete-verdict").waitFor({ timeout: 15000 });
  await shot(page, "01_reference_complete_status.png", "Reference complete PASS panel");

  await page.getByTestId("reference-complete-limitations").click();
  await shot(page, "02_accepted_limitations.png", "Accepted limitations");

  await page.getByTestId("product-system-template-detail-tab-pricing").click();
  await page.getByTestId("price-breakdown-totals").waitFor({ timeout: 45000 });
  await shot(page, "03_eic_cpp_distinction.png", "EIC vs CPP production-cost view");

  await page.goto(`${BASE}/inventory/pricing`, { waitUntil: "networkidle", timeout: 60000 });
  await page.getByRole("button", { name: /Preturi materiale/i }).first().click();
  await page.getByTestId("material-market-price-registry").waitFor({ timeout: 45000 });
  await page.getByTestId("material-market-row-MAT-LED-PSU-12V").scrollIntoViewIfNeeded();
  await page.getByTestId("material-market-row-MAT-LED-PSU-12V").click();
  await shot(page, "04_psu_selector_and_zero_critical.png", "PSU selector + critical cleared");

  fs.writeFileSync(path.join(OUT, "capture_log.json"), JSON.stringify({ base: BASE, shots }, null, 2));
  await browser.close();
  console.log("Done", shots.length);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
