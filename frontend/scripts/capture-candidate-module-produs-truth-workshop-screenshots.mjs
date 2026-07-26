import { chromium } from "playwright";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.resolve(__dirname, "../../docs/qa/candidate-module-letters-product-truth-workshop-v1/screenshots");
const BASE = process.env.PW_BASE_URL ?? "http://127.0.0.1:3000";

const BUCKET = {
  candidateModuleProdus: "product-system-catalog-bucket-candidate-module-sets",
  candidateModuleProdusToggle: "product-system-catalog-bucket-toggle-candidate-module-sets",
  legacy: "product-system-catalog-bucket-legacy-shared-modules",
  legacyToggle: "product-system-catalog-bucket-toggle-legacy-shared-modules",
  candidateProducts: "product-system-catalog-bucket-candidate-products",
  candidateProductsToggle: "product-system-catalog-bucket-toggle-candidate-products",
};

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

await page.getByTestId("product-system-canonical-filter-deprecated").click();
await page.locator(`[data-testid="product-system-canonical-catalog-card"][data-template-code="TPL-LETTERS-COMPOSER_v1"]`).click();
await page.getByTestId("product-system-template-detail-tab-dossier").click();
await page.getByTestId("product-system-template-detail-open-editor").click();
await page.getByTestId("product-system-candidate-module-tab-guards-audit").click();
await page.getByTestId("product-system-truth-owner-workshop").waitFor({ timeout: 15_000 });

await shot(page, "01_candidate_module_workshop_entry");

await page.getByTestId("product-system-truth-workshop-tab-RETURN-CANT").click();
await page.getByTestId("product-system-truth-workshop-fields-table-RETURN-CANT").scrollIntoViewIfNeeded();
await shot(page, "02_return_cant_fields_table");

await page.getByTestId("product-system-truth-workshop-owner-questions").scrollIntoViewIfNeeded();
await shot(page, "03_return_cant_owner_questions");

await page.getByTestId("product-system-truth-workshop-global-status").scrollIntoViewIfNeeded();
await shot(page, "04_owner_input_required_status");

await page.getByTestId("product-system-truth-workshop-safety-copy").scrollIntoViewIfNeeded();
await shot(page, "05_safety_copy_no_write_pricing_wi");

await page.getByTestId("product-system-truth-workshop-questions-skeleton").scrollIntoViewIfNeeded();
await shot(page, "06_skeleton_questions_other_components");

await page.getByTestId("product-system-unified-row-TPL-VOLUMETRIC-LETTERS_v2").click();
await page.getByTestId("product-system-template-detail-overview").waitFor({ timeout: 10_000 });
await shot(page, "07_active_root_work_intake_offerable");

await expand(page, BUCKET.candidateProducts, BUCKET.candidateProductsToggle);
await page.getByTestId("product-system-unified-row-TPL-VOLUMETRIC-LOGO_v1").click();
await shot(page, "08_logo_not_work_intake_owner_go");

await expand(page, BUCKET.legacy, BUCKET.legacyToggle);
await page.getByTestId("product-system-legacy-bucket-view-replacement-map").click();
await page.getByTestId("product-system-legacy-replacement-global-verdict").waitFor({ timeout: 10_000 });
await shot(page, "09_legacy_replacement_not_ready_for_delete");

await page.evaluate(() => window.scrollTo(0, 0));
await shot(page, "10_no_save_activate_promote_buttons");

await browser.close();
console.log(`Screenshots saved to ${OUT}`);
