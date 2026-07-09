import { chromium } from "playwright";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.resolve(
  __dirname,
  "../../docs/qa/component-first-return-cant-catalog-price-inputs-workshop-v1/screenshots",
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
await page.getByTestId("product-system-return-cant-catalog-price-inputs").waitFor({ timeout: 15_000 });

await shot(page, "01_catalog_price_inputs_panel");

await page.getByTestId("product-system-return-cant-catalog-price-global-status").scrollIntoViewIfNeeded();
await shot(page, "02_not_ready_for_pricing_summary");

await page.getByTestId("product-system-return-cant-catalog-price-section-oracal_catalog").scrollIntoViewIfNeeded();
await shot(page, "03_oracal_catalog_section");

await page.getByTestId("product-system-return-cant-catalog-price-section-oracal_pricing").scrollIntoViewIfNeeded();
await shot(page, "04_oracal_pricing_section");

await page.getByTestId("product-system-return-cant-catalog-price-section-ral_catalog").scrollIntoViewIfNeeded();
await shot(page, "05_ral_catalog_section");

await page.getByTestId("product-system-return-cant-catalog-price-section-ral_material_pricing").scrollIntoViewIfNeeded();
await shot(page, "06_ral_material_labor_pricing_section");

await page
  .getByTestId("product-system-return-cant-catalog-price-row-return_material_depth_compatibility")
  .scrollIntoViewIfNeeded();
await shot(page, "07_material_depth_compatibility_row");

await page.getByTestId("product-system-return-cant-catalog-price-safety").scrollIntoViewIfNeeded();
await shot(page, "08_safety_copy_no_write_no_pricing");

await page.getByTestId("product-system-return-cant-catalog-price-blockers").scrollIntoViewIfNeeded();
await shot(page, "09_no_save_apply_pricing_actions");

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
