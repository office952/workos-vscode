/**
 * PRODUCT_SYSTEM_REFERENCE_FINISH_LINE_V1 — screenshot pack.
 * FE must proxy to backend :8020 (BACKEND_PORT=8020).
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

  await page.goto(`${BASE}/product-system`, { waitUntil: "networkidle", timeout: 60000 });
  await shot(page, "01_product_system_index.png", "Product System overview");

  await page.goto(`${BASE}/product-system/products/TPL-VOLUMETRIC-LETTERS_v2`, {
    waitUntil: "networkidle",
    timeout: 60000,
  });
  await page.getByTestId("reference-finish-line-panel").waitFor({ timeout: 45000 });
  await shot(page, "02_vl_overview_finish_line.png", "VL overview + finish-line panel");

  await page.getByTestId("product-system-template-detail-tab-composition").click();
  await page.getByTestId("composition-authoring-lab-limitation").waitFor({ timeout: 30000 });
  await shot(page, "03_vl_composition_option2.png", "Composition authoring Option 2 banner");

  await page.getByTestId("product-system-template-detail-tab-pricing").click();
  await page.getByTestId("price-breakdown-section").waitFor({ timeout: 45000 });
  await shot(page, "04_vl_production_cost_labels.png", "EIC Cost productie vs CPP");
  await page.getByTestId("price-breakdown-totals").scrollIntoViewIfNeeded();
  await shot(page, "05_vl_eic_cpp_totals.png", "Totals Cost productie / Pret comercial");

  await page.goto(`${BASE}/product-system/products/TPL-VOLUM-ALUMINIU_v1`, {
    waitUntil: "networkidle",
    timeout: 60000,
  });
  await shot(page, "06_volum_aluminiu_child.png", "Volum Aluminiu child detail");

  await page.goto(`${BASE}/product-system/products/TPL-ACM-BOXED-MOUNTING-SUPPORT_v1`, {
    waitUntil: "networkidle",
    timeout: 60000,
  });
  await shot(page, "07_acm_shell.png", "ACM optional capability shell");

  await page.goto(`${BASE}/product-system/products/TPL-VOLUMETRIC-LOGO_v1`, {
    waitUntil: "networkidle",
    timeout: 60000,
  });
  await shot(page, "08_logo_incomplete.png", "Logo incomplete path");

  await page.goto(`${BASE}/inventory/pricing`, { waitUntil: "networkidle", timeout: 60000 });
  await shot(page, "09_material_pricing.png", "Preturi materiale / critical context");

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
