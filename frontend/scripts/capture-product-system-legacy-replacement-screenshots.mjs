import { chromium } from "playwright";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.resolve(__dirname, "../../docs/qa/product-system-legacy-replacement-map-v1/screenshots");
const BASE = process.env.PW_BASE_URL ?? "http://127.0.0.1:3000";

const BUCKET = {
  legacy: "product-system-catalog-bucket-legacy-shared-modules",
  legacyToggle: "product-system-catalog-bucket-toggle-legacy-shared-modules",
  candidateModuleProdus: "product-system-catalog-bucket-candidate-module-sets",
  candidateModuleProdusToggle: "product-system-catalog-bucket-toggle-candidate-module-sets",
};

async function expand(page, bucketId, toggleId) {
  const bucket = page.getByTestId(bucketId);
  if ((await bucket.getAttribute("data-expanded")) !== "true") {
    await page.getByTestId(toggleId).click();
    await bucket.waitFor({ state: "visible" });
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

await shot(page, "01_product_system_catalog");

const legacyBucket = page.getByTestId(BUCKET.legacy);
await legacyBucket.scrollIntoViewIfNeeded();
await shot(page, "02_legacy_bucket_collapsed");

await expand(page, BUCKET.legacy, BUCKET.legacyToggle);
await page.getByTestId("product-system-legacy-bucket-support-copy").waitFor({ timeout: 15_000 });
await shot(page, "03_legacy_bucket_expanded_banner");

await page.getByTestId("product-system-legacy-bucket-view-replacement-map").click();
await page.getByTestId("product-system-legacy-replacement-readiness").waitFor({ timeout: 15_000 });
await shot(page, "04_legacy_replacement_readiness_table");

await page.getByTestId("product-system-legacy-replacement-row-TPL-VOLUMETRIC-FACE_v1").scrollIntoViewIfNeeded();
await shot(page, "05_mapping_face");

await page.getByTestId("product-system-legacy-replacement-row-TPL-VOLUM-ALUMINIU_v1").scrollIntoViewIfNeeded();
await shot(page, "06_mapping_return_cant");

await page.getByTestId("product-system-legacy-replacement-row-TPL-VOLUMETRIC-LED_v1").scrollIntoViewIfNeeded();
await shot(page, "07_mapping_led");

await page.getByTestId("product-system-legacy-replacement-global-verdict").scrollIntoViewIfNeeded();
await shot(page, "08_not_ready_for_delete_summary");

await expand(page, BUCKET.candidateModuleProdus, BUCKET.candidateModuleProdusToggle);
await page.getByTestId("product-system-canonical-filter-deprecated").click();
await page.locator(`[data-testid="product-system-canonical-catalog-card"][data-template-code="TPL-LETTERS-COMPOSER_v1"]`).click();
await page.getByTestId("product-system-template-detail-tab-dossier").click();
await page.getByTestId("product-system-template-detail-open-editor").click();
await page.getByTestId("product-system-candidate-module-replacement-context").waitFor({ timeout: 15_000 });
await shot(page, "09_component_first_replacement_context");

await page.evaluate(() => window.scrollTo(0, 0));
await shot(page, "10_no_delete_activate_actions");

await browser.close();
console.log(`Screenshots saved to ${OUT}`);
