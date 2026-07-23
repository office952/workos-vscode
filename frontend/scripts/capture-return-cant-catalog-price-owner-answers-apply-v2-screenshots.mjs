import { chromium } from "playwright";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.resolve(
  __dirname,
  "../../docs/qa/candidate-module-return-cant-catalog-price-owner-answers-apply-v2/screenshots",
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
  "product-system-catalog-bucket-candidate-module-sets",
  "product-system-catalog-bucket-toggle-candidate-module-sets",
);
await page.getByTestId("product-system-canonical-filter-deprecated").click();
await page.locator(`[data-testid="product-system-canonical-catalog-card"][data-template-code="TPL-LETTERS-COMPOSER_v1"]`).click();
await page.getByTestId("product-system-template-detail-tab-dossier").click();
await page.getByTestId("product-system-template-detail-open-editor").click();
await page.getByTestId("product-system-candidate-module-tab-guards-audit").click();
await page.getByTestId("product-system-return-cant-catalog-price-inputs").waitFor({ timeout: 15_000 });

await shot(page, "01_catalog_price_panel_after_owner_answers");

await page.getByTestId("product-system-return-cant-catalog-price-value-oracal_calculation_model").scrollIntoViewIfNeeded();
await shot(page, "02_oracal_calculation_model_roll_widths");

await page.getByTestId("product-system-return-cant-catalog-price-value-oracal_price_table").scrollIntoViewIfNeeded();
await shot(page, "03_oracal_pricing_mode_missing_table_values");

await page.getByTestId("product-system-return-cant-catalog-price-value-ral_selector_source").scrollIntoViewIfNeeded();
await shot(page, "04_ral_classic_selector_source");

await page.getByTestId("product-system-return-cant-catalog-price-value-ral_material_price_by_depth").scrollIntoViewIfNeeded();
await shot(page, "05_ral_material_prices_by_depth");

await page.getByTestId("product-system-return-cant-catalog-price-value-ral_labor_price_by_depth").scrollIntoViewIfNeeded();
await shot(page, "06_ral_labor_price_all_depths");

await page.getByTestId("product-system-return-cant-catalog-price-value-ral_minimum_rule").scrollIntoViewIfNeeded();
await shot(page, "07_ral_minimum_100_lei_scope_pending");

await page
  .getByTestId("product-system-return-cant-catalog-price-value-return_material_depth_compatibility")
  .scrollIntoViewIfNeeded();
await shot(page, "08_material_depth_compatibility_al_06");

await page.getByTestId("product-system-return-cant-catalog-price-global-status").scrollIntoViewIfNeeded();
await shot(page, "09_not_ready_for_pricing_safety_copy");

await page.getByTestId("product-system-return-cant-catalog-price-blockers").scrollIntoViewIfNeeded();
await shot(page, "10_no_save_apply_pricing_actions");

await page.getByTestId("product-system-unified-row-TPL-VOLUMETRIC-LETTERS_v2").click();
await shot(page, "11_active_root_offerable_work_intake");

await expand(
  page,
  "product-system-catalog-bucket-candidate-products",
  "product-system-catalog-bucket-toggle-candidate-products",
);
await page.getByTestId("product-system-unified-row-TPL-VOLUMETRIC-LOGO_v1").click();
await shot(page, "12_logo_not_work_intake_owner_go");

await browser.close();
console.log(`Screenshots saved to ${OUT}`);
