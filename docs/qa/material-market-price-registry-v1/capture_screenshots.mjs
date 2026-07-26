/**
 * MATERIAL_MARKET_PRICE_REGISTRY_V1 — screenshot pack.
 * FE must proxy to :8020 (BACKEND_PORT=8020).
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
  await shot(page, "01_pricing_overview.png", "Pricing overview");

  // Open Preturi materiale catalog filter
  const matTab = page.getByRole("button", { name: /Preturi materiale/i }).first();
  await matTab.click();
  await page.getByTestId("material-market-price-registry").waitFor({ timeout: 45000 });
  await shot(page, "02_material_registry.png", "Material market registry");

  await page.getByTestId("material-market-filter-missing").click();
  await shot(page, "03_missing_prices.png", "Missing prices filter");

  await page.getByTestId("material-market-filter-priced").click();
  const acm = page.getByTestId("material-market-row-MAT-ACM-BOND-3MM");
  if (await acm.count()) {
    await acm.click();
    await shot(page, "04_acm_3mm_detail.png", "ACM 3mm priced detail");
  } else {
    const first = page.locator("[data-testid^=material-market-row-]").first();
    await first.click();
    await shot(page, "04_priced_detail.png", "Priced material detail");
  }

  await page.getByTestId("material-market-filter-all").click();
  await shot(page, "05_registry_full.png", "Full registry");

  // Product System VL breakdown materials
  await page.goto(
    `${BASE}/product-system/products/${encodeURIComponent("TPL-VOLUMETRIC-LETTERS_v2")}`,
    { waitUntil: "networkidle", timeout: 60000 },
  );
  await page.getByTestId("product-system-template-detail-tab-pricing").click();
  await page.getByTestId("price-breakdown-section").waitFor({ timeout: 45000 });
  await page.getByTestId("price-breakdown-filter-material").click();
  await shot(page, "06_vl_material_breakdown.png", "VL material breakdown provenance");

  await page.goto(
    `${BASE}/product-system/products/${encodeURIComponent("TPL-ACM-BOXED-MOUNTING-SUPPORT_v1")}`,
    { waitUntil: "networkidle", timeout: 60000 },
  );
  await page.getByTestId("product-system-template-detail-tab-pricing").click();
  await page.getByTestId("price-breakdown-section").waitFor({ timeout: 45000 });
  await shot(page, "07_acm_breakdown.png", "ACM breakdown");

  fs.writeFileSync(
    path.join(OUT, "capture_log.json"),
    JSON.stringify({ base: BASE, shots }, null, 2),
    "utf8",
  );
  await browser.close();
  console.log("Done", shots.length);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
