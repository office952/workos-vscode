import { chromium } from "playwright";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.resolve(__dirname, "../../docs/qa/return-cant-ral-pricing-key-dedup-v1/screenshots");
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
await page.getByTestId("product-system-return-cant-catalog-price-inputs").waitFor({ timeout: 15_000 });

await shot(page, "01_return_cant_catalog_price_inputs_after_ral_dedup");

await page.getByTestId("product-system-return-cant-catalog-price-ral-series-summary").scrollIntoViewIfNeeded();
await shot(page, "02_ral_material_keys_visible");

await page.getByTestId("product-system-return-cant-ral-labor-price").scrollIntoViewIfNeeded();
await shot(page, "03_ral_labor_key_visible");

await page.getByTestId("product-system-return-cant-ral-pricing-source").scrollIntoViewIfNeeded();
await shot(page, "04_inventory_pricing_source_visible");

await page.getByTestId("product-system-return-cant-ral-minimum-owner-policy").scrollIntoViewIfNeeded();
await shot(page, "05_ral_minimum_100_lei_owner_commercial_rule");

await page.getByTestId("product-system-return-cant-ral-minimum-policy").scrollIntoViewIfNeeded();
await shot(page, "06_not_in_pricing_registry_for_minimum");

await page.getByTestId("product-system-return-cant-catalog-price-global-status").scrollIntoViewIfNeeded();
await shot(page, "07_not_ready_for_pricing_still_visible");

await page.getByTestId("product-system-return-cant-catalog-price-safety").scrollIntoViewIfNeeded();
await shot(page, "08_no_save_apply_pricing_activation_actions");

await page.getByTestId("product-system-unified-row-TPL-VOLUMETRIC-LETTERS_v2").click();
await shot(page, "09_active_root_offerable_work_intake_yes");

await expand(
  page,
  "product-system-catalog-bucket-candidate-products",
  "product-system-catalog-bucket-toggle-candidate-products",
);
await page.getByTestId("product-system-unified-row-TPL-VOLUMETRIC-LOGO_v1").click();
await shot(page, "10_logo_not_work_intake_owner_go");

await browser.close();
console.log(`Screenshots saved to ${OUT}`);
