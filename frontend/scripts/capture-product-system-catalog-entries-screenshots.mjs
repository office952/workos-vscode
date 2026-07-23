/**
 * Screenshot capture for PRODUCT_SYSTEM_UNIFIED_CATALOG_MASTER_DETAIL_CORRECTION_V1
 * Requires frontend dev server on :3000
 */
import { chromium } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const outDir = path.resolve(
  __dirname,
  "../../docs/qa/product-system-unified-catalog-2026-07-09/screenshots",
);

async function shotPage(page, name) {
  const file = path.join(outDir, `${name}.png`);
  await page.screenshot({ path: file, fullPage: true });
  console.log("saved", file);
}

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

  await shotViewport(page, "01_unified_catalog_search_filter_list");
  await page.getByTestId("product-system-unified-row-TPL-VOLUMETRIC-LETTERS_v2").scrollIntoViewIfNeeded();
  await shotViewport(page, "02_unified_list_tpl_volumetric_letters_v2");
  await page.getByTestId("product-system-canonical-filter-deprecated").click();
  await shotViewport(page, "03_unified_list_component_first_candidate");

  await page.getByTestId("product-system-unified-row-TPL-VOLUMETRIC-LETTERS_v2").click();
  await page.waitForSelector('[data-testid="product-system-template-detail-panel"]', { timeout: 15000 });
  await shotViewport(page, "04_selected_tpl_volumetric_detail_panel");

  await page.getByTestId("product-system-canonical-filter-deprecated").click();
await page.locator(`[data-testid="product-system-canonical-catalog-card"][data-template-code="TPL-LETTERS-COMPOSER_v1"]`).click();
await page.getByTestId("product-system-template-detail-tab-dossier").click();
await page.getByTestId("product-system-template-detail-open-editor").click();
  await page.waitForSelector('[data-testid="product-system-candidate-module-letters-set"]', { timeout: 15000 });
  await shotViewport(page, "05_selected_candidate_detail_panel");

  await page.getByTestId("product-system-candidate-module-tab-components").click();
  await page.waitForTimeout(300);
  await shotViewport(page, "06_candidate_detail_components_table");

  await page.getByTestId("product-system-candidate-module-tab-dossier").click();
  await page.waitForTimeout(300);
  await shotViewport(page, "07_candidate_detail_dossier");

  await page.getByTestId("product-system-candidate-module-tab-guards-audit").click();
  await page.waitForTimeout(300);
  await shotViewport(page, "08_candidate_detail_guards");

  await page.goto("http://127.0.0.1:3000/product-system", { waitUntil: "networkidle", timeout: 120000 });
  await page.waitForSelector('[data-testid="product-system-unified-filter-chips"]', { timeout: 60000 });
  await shotViewport(page, "09_proof_no_six_top_level_tabs");

  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await page.waitForTimeout(300);
  await shotViewport(page, "10_proof_no_existing_roots_bottom_block");

  await browser.close();
  console.log("done");
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
