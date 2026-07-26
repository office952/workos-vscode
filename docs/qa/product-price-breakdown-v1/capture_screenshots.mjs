/**
 * PRODUCT_PRICE_BREAKDOWN_V1 — screenshot pack (Playwright).
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

async function openPricing(page, templateCode) {
  const url = `${BASE}/product-system/products/${encodeURIComponent(templateCode)}`;
  await page.goto(url, { waitUntil: "networkidle", timeout: 60000 });
  const tab = page.getByTestId("product-system-template-detail-tab-pricing");
  await tab.click();
  await page.getByTestId("price-breakdown-section").waitFor({ timeout: 45000 });
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1100 } });

  await openPricing(page, "TPL-VOLUMETRIC-LETTERS_v2");
  await shot(page, "01_vl_overview.png", "VL Desfășurător pret overview");
  await page.getByTestId("price-breakdown-totals").scrollIntoViewIfNeeded();
  await shot(page, "02_vl_totals.png", "VL totals + reconcile");
  await page.getByTestId("price-breakdown-filter-material").click();
  await shot(page, "03_vl_materials.png", "VL materials filter");
  await page.getByTestId("price-breakdown-filter-machine").click();
  await shot(page, "04_vl_machine.png", "VL machine ops");
  await page.getByTestId("price-breakdown-filter-labor").click();
  await shot(page, "05_vl_labor.png", "VL labor");
  await page.getByTestId("price-breakdown-filter-ai_decision").click();
  await shot(page, "06_vl_ai.png", "VL AI decisions");
  await page.getByTestId("price-breakdown-filter-all").click();
  await shot(page, "07_vl_full_page.png", "VL full page reconcile");

  await openPricing(page, "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1");
  await shot(page, "08_acm_shell.png", "ACM shell breakdown");
  const acmTreat = page.getByTestId("price-breakdown-acm-treatments-blocked");
  if (await acmTreat.count()) {
    await shot(page, "09_acm_treatments_blocked.png", "ACM treatments blocked chip");
  }

  await openPricing(page, "TPL-VOLUMETRIC-LOGO_v1");
  await shot(page, "10_logo_preview.png", "Logo preview + publication honesty");

  await openPricing(page, "TPL-VOLUM-ALUMINIU_v1");
  await shot(page, "11_volum_aluminiu_child.png", "Volum Aluminiu child breakdown");

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
