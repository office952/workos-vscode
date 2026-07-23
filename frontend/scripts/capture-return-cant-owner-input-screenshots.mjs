import { chromium } from "playwright";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.resolve(__dirname, "../../docs/qa/candidate-module-return-cant-owner-input-apply-v1/screenshots");
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

await expand(page, "product-system-catalog-bucket-candidate-module-sets", "product-system-catalog-bucket-toggle-candidate-module-sets");
await page.getByTestId("product-system-canonical-filter-deprecated").click();
await page.locator(`[data-testid="product-system-canonical-catalog-card"][data-template-code="TPL-LETTERS-COMPOSER_v1"]`).click();
await page.getByTestId("product-system-template-detail-tab-dossier").click();
await page.getByTestId("product-system-template-detail-open-editor").click();
await page.getByTestId("product-system-candidate-module-tab-guards-audit").click();
await page.getByTestId("product-system-truth-owner-workshop").waitFor({ timeout: 15_000 });

await shot(page, "01_component_first_workshop_panel");

await page.getByTestId("product-system-return-cant-owner-inputs").scrollIntoViewIfNeeded();
await shot(page, "02_return_cant_owner_inputs");

await page.getByTestId("product-system-return-cant-confirmed-so-far").scrollIntoViewIfNeeded();
await shot(page, "03_confirmed_so_far");

await page.getByTestId("product-system-return-cant-missing-before-pricing").scrollIntoViewIfNeeded();
await shot(page, "04_still_missing_before_pricing");

await page.getByTestId("product-system-return-cant-missing-before-product-definition").scrollIntoViewIfNeeded();
await shot(page, "05_still_missing_before_product_definition");

await page.getByTestId("product-system-return-cant-owner-questions-pending").scrollIntoViewIfNeeded();
await shot(page, "06_owner_questions_table");

await page.getByTestId("product-system-return-cant-owner-inputs-safety").scrollIntoViewIfNeeded();
await shot(page, "07_safety_copy");

await page.getByTestId("product-system-unified-row-TPL-VOLUMETRIC-LETTERS_v2").click();
await shot(page, "08_active_root_offerable_work_intake");

await expand(page, "product-system-catalog-bucket-candidate-products", "product-system-catalog-bucket-toggle-candidate-products");
await page.getByTestId("product-system-unified-row-TPL-VOLUMETRIC-LOGO_v1").click();
await shot(page, "09_logo_not_work_intake_owner_go");

await expand(page, "product-system-catalog-bucket-legacy-shared-modules", "product-system-catalog-bucket-toggle-legacy-shared-modules");
await page.getByTestId("product-system-legacy-bucket-view-replacement-map").click();
await page.getByTestId("product-system-legacy-replacement-global-verdict").waitFor({ timeout: 10_000 });
await shot(page, "10_legacy_not_ready_for_delete");

await browser.close();
console.log(`Screenshots saved to ${OUT}`);
