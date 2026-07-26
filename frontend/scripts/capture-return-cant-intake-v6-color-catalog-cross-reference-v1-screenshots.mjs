import { chromium } from "playwright";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.resolve(
  __dirname,
  "../../docs/qa/candidate-module-return-cant-intake-v6-color-catalog-cross-reference-v1/screenshots",
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

await shot(page, "01_return_cant_catalog_price_panel");

await page.getByTestId("product-system-return-cant-catalog-price-known-oracal_catalog_source").scrollIntoViewIfNeeded();
await shot(page, "02_oracal_intake_v6_source_cross_reference");

await page.getByTestId("product-system-return-cant-catalog-price-known-ral_catalog_source").scrollIntoViewIfNeeded();
await shot(page, "03_ral_intake_v6_source_cross_reference");

await page.getByTestId("product-system-return-cant-catalog-price-oracal-series-summary").scrollIntoViewIfNeeded();
await shot(page, "04_oracal_prices_651_641_8500");

await page.getByTestId("product-system-return-cant-catalog-price-value-oracal_calculation_model").scrollIntoViewIfNeeded();
await shot(page, "05_oracal_mp_calculation_roll_widths");

await page.getByTestId("product-system-return-cant-catalog-price-value-ral_material_price_by_depth").scrollIntoViewIfNeeded();
await shot(page, "06_ral_values_unchanged");

await page.getByTestId("product-system-return-cant-catalog-price-global-status").scrollIntoViewIfNeeded();
await shot(page, "07_not_ready_for_pricing_blockers");

await page.getByTestId("product-system-return-cant-catalog-price-safety").scrollIntoViewIfNeeded();
await shot(page, "08_no_save_apply_pricing_actions");

await page.getByTestId("product-system-unified-row-TPL-VOLUMETRIC-LETTERS_v2").click();
await shot(page, "09_active_root_offerable_work_intake");

await expand(
  page,
  "product-system-catalog-bucket-candidate-products",
  "product-system-catalog-bucket-toggle-candidate-products",
);
await page.getByTestId("product-system-unified-row-TPL-VOLUMETRIC-LOGO_v1").click();
await shot(page, "10_logo_not_work_intake_owner_go");

await browser.close();
console.log(`Screenshots saved to ${OUT}`);
