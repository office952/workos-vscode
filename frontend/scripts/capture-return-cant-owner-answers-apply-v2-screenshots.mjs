import { chromium } from "playwright";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.resolve(
  __dirname,
  "../../docs/qa/component-first-return-cant-owner-answers-apply-v2/screenshots",
);
const BASE = process.env.PW_BASE_URL ?? "http://127.0.0.1:3000";

async function expand(page, bucketId, toggleId) {
  const bucket = page.getByTestId(bucketId);
  if ((await bucket.getAttribute("data-expanded")) !== "true") {
    await page.getByTestId(toggleId).click();
  }
}

async function shot(page, name) {
  await mkdir(OUT, { recursive: true });
  await page.screenshot({ path: path.join(OUT, `${name}.png`), fullPage: false });
}

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
await page.goto(`${BASE}/product-system`, { waitUntil: "domcontentloaded", timeout: 120_000 });
await page.getByTestId("product-system-unified-catalog").waitFor({ timeout: 60_000 });

await expand(
  page,
  "product-system-catalog-bucket-component-first-sets",
  "product-system-catalog-bucket-toggle-component-first-sets",
);
await page.getByTestId("product-system-unified-row-candidate-set").click();
await page.getByTestId("product-system-component-first-tab-guards-audit").click();
await page.getByTestId("product-system-truth-owner-workshop").waitFor({ timeout: 15_000 });

await page.getByTestId("product-system-return-cant-owner-inputs").scrollIntoViewIfNeeded();
await shot(page, "01_return_cant_owner_inputs_after_owner_answers");

await page.getByTestId("product-system-return-cant-owner-input-value-oracal_selector_mode").scrollIntoViewIfNeeded();
await shot(page, "02_confirmed_oracal_selector_pricing");

await page.getByTestId("product-system-return-cant-owner-input-value-ral_input_mode").scrollIntoViewIfNeeded();
await shot(page, "03_confirmed_ral_selector_mode");

await page.getByTestId("product-system-return-cant-owner-input-value-return_depths_standard").scrollIntoViewIfNeeded();
await shot(page, "04_confirmed_depths_30_60_80_100");

await page
  .getByTestId("product-system-return-cant-owner-input-value-return_material")
  .scrollIntoViewIfNeeded();
await shot(page, "05_confirmed_material_and_units_ml");

await page
  .getByTestId("product-system-return-cant-owner-input-value-ral_material_price_rule")
  .scrollIntoViewIfNeeded();
await shot(page, "06_partial_ral_material_labor_prices_missing");

await page
  .getByTestId("product-system-return-cant-owner-input-value-stock_color_affects_price")
  .scrollIntoViewIfNeeded();
await shot(page, "07_stock_color_no_pricing_impact");

await page
  .getByTestId("product-system-return-cant-owner-input-value-perimeter_geometry_source")
  .scrollIntoViewIfNeeded();
await shot(page, "08_geometry_perimeter_source_confirmed");

await page.getByTestId("product-system-return-cant-owner-inputs-safety").scrollIntoViewIfNeeded();
await shot(page, "09_safety_copy_no_write_no_pricing");

await page.getByTestId("product-system-unified-row-TPL-VOLUMETRIC-LETTERS_v2").click();
await shot(page, "10_active_root_offerable_work_intake");

await expand(
  page,
  "product-system-catalog-bucket-candidate-products",
  "product-system-catalog-bucket-toggle-candidate-products",
);
await page.getByTestId("product-system-unified-row-TPL-VOLUMETRIC-LOGO_v1").click();
await shot(page, "11_logo_not_work_intake_owner_go");

await browser.close();
console.log(`Screenshots saved to ${OUT}`);
