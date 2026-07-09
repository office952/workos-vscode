/**
 * Screenshot capture for PRODUCT_SYSTEM_UNIFIED_CATALOG_BUCKET_SEPARATION_V1
 * Requires frontend dev server on :3000
 */
import { chromium } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const outDir = path.resolve(
  __dirname,
  "../../docs/qa/product-system-unified-catalog-buckets-2026-07-09/screenshots",
);

async function shotViewport(page, name) {
  const file = path.join(outDir, `${name}.png`);
  await page.screenshot({ path: file, fullPage: false });
  console.log("saved", file);
}

async function main() {
  await mkdir(outDir, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  await page.goto("http://127.0.0.1:3000/product-system", { waitUntil: "networkidle", timeout: 120000 });
  await page.waitForSelector('[data-testid="product-system-unified-catalog"]', { timeout: 60000 });

  await shotViewport(page, "01_default_bucketed_catalog_view");
  await shotViewport(page, "02_current_products_bucket_letters_v2");

  await page.getByTestId("product-system-catalog-bucket-candidate-products").scrollIntoViewIfNeeded();
  await shotViewport(page, "03_candidate_products_bucket");

  await page.getByTestId("product-system-catalog-bucket-component-first-sets").scrollIntoViewIfNeeded();
  await shotViewport(page, "04_component_first_candidate_sets_bucket");

  await page.getByTestId("product-system-unified-row-candidate-set").click();
  await page.waitForSelector('[data-testid="product-system-component-first-letters-set"]', { timeout: 15000 });
  await page.getByTestId("product-system-component-first-tab-components").click();
  await page.waitForTimeout(300);
  await shotViewport(page, "05_component_first_detail_composer_and_components");

  await page.getByTestId("product-system-catalog-bucket-toggle-legacy-shared-modules").scrollIntoViewIfNeeded();
  await shotViewport(page, "06_legacy_shared_modules_collapsed");

  await page.getByTestId("product-system-catalog-bucket-toggle-legacy-shared-modules").click();
  await page.waitForTimeout(400);
  await shotViewport(page, "07_legacy_shared_modules_expanded");

  await page.getByTestId("product-system-unified-row-TPL-VOLUMETRIC-LETTERS_v2").click();
  await page.waitForSelector('[data-testid="product-system-template-detail-bucket-headline"]', { timeout: 15000 });
  await shotViewport(page, "08_letters_detail_current_active_root");

  const logoRow = page.getByTestId("product-system-unified-row-TPL-VOLUMETRIC-LOGO_v1");
  if (await logoRow.count()) {
    await logoRow.click();
    await page.waitForTimeout(400);
    await shotViewport(page, "09_logo_detail_not_work_intake_owner_go");
  } else {
    console.log("skip 09 — LOGO row not in live catalog");
  }

  await page.goto("http://127.0.0.1:3000/product-system", { waitUntil: "networkidle", timeout: 120000 });
  await page.waitForSelector('[data-testid="product-system-catalog-bucket-current-products"]', { timeout: 60000 });
  await shotViewport(page, "10_proof_bucketed_not_flat_mixed_list");

  await browser.close();
  console.log("done");
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
