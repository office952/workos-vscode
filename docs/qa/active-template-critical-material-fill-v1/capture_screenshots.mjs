/**
 * ACTIVE_TEMPLATE_CRITICAL_MATERIAL_FILL_V1 — screenshot pack.
 * FE proxies to :8020.
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

  await page.goto(`${BASE}/inventory/pricing`, { waitUntil: "networkidle", timeout: 60000 });
  await page.getByRole("button", { name: /Preturi materiale/i }).first().click();
  await page.getByTestId("material-market-price-registry").waitFor({ timeout: 45000 });
  await shot(page, "01_material_pricing_overview.png", "Preturi materiale overview");

  await page.getByTestId("material-market-filter-all").click();
  const generic = page.getByTestId("material-market-row-MAT-LED-PSU-12V");
  await generic.scrollIntoViewIfNeeded();
  await generic.click();
  await page.getByTestId("material-market-selector-note").waitFor({ timeout: 15000 });
  await shot(page, "02_psu_selector_generic.png", "Generic PSU selector identity");

  const v100 = page.getByTestId("material-market-row-MAT-LED-PSU-12V-100W");
  await v100.scrollIntoViewIfNeeded();
  await v100.click();
  await shot(page, "03_psu_variant_100w.png", "Concrete 100W OWNER_CONFIRMED");

  await page.goto(`${BASE}/product-system/products/TPL-VOLUMETRIC-LETTERS_v2`, {
    waitUntil: "networkidle",
    timeout: 60000,
  });
  await page.getByTestId("reference-finish-line-panel").waitFor({ timeout: 45000 });
  await shot(page, "04_finish_line_critical_cleared.png", "Finish-line critical panel");

  await page.getByTestId("product-system-template-detail-tab-pricing").click();
  await page.getByTestId("price-breakdown-section").waitFor({ timeout: 45000 });
  await page.getByTestId("price-breakdown-filter-material").click();
  await shot(page, "05_vl_breakdown_materials.png", "VL materials incl concrete PSU");
  await page.getByTestId("price-breakdown-totals").scrollIntoViewIfNeeded();
  await shot(page, "06_vl_eic_cpp_reconcile.png", "VL EIC/CPP still reconciled");

  fs.writeFileSync(
    path.join(OUT, "capture_log.json"),
    JSON.stringify({ base: BASE, shots }, null, 2),
    "utf8",
  );
  await browser.close();
  console.log("Done", shots.length, "screenshots");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
