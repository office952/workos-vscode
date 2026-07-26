/**
 * Screenshot capture for PRODUCT_SYSTEM_BUCKETED_CATALOG_COMPACT_LAYOUT_V1
 * Requires frontend dev server on :3000
 */
import { chromium } from "@playwright/test";
import { copyFile, mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const outDir = path.resolve(
  __dirname,
  "../../docs/qa/product-system-bucketed-catalog-compact-layout-2026-07-09/screenshots",
);
const beforeDir = path.resolve(
  __dirname,
  "../../docs/qa/product-system-unified-catalog-ui-polish-2026-07-09/screenshots",
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
  await page.waitForSelector('[data-testid="product-system-unified-catalog"][data-layout="compact"]', {
    timeout: 60000,
  });

  await shotViewport(page, "01_top_viewport_compact_layout");
  await shotViewport(page, "02_catalog_buckets_visible_high");

  await page.getByTestId("product-system-catalog-bucket-current-products").scrollIntoViewIfNeeded();
  await shotViewport(page, "03_current_products_bucket");

  await page.getByTestId("product-system-catalog-bucket-candidate-products").scrollIntoViewIfNeeded();
  await page.getByTestId("product-system-catalog-bucket-candidate-module-sets").scrollIntoViewIfNeeded();
  await shotViewport(page, "04_candidate_and_component_first_buckets");

  await page.getByTestId("product-system-unified-row-TPL-VOLUMETRIC-LETTERS_v2").click();
  await page.waitForSelector('[data-testid="product-system-template-detail-bucket-headline"]', { timeout: 15000 });
  await shotViewport(page, "05_detail_panel_aligned_with_buckets");

  await page.getByTestId("product-system-catalog-bucket-toggle-legacy-shared-modules").scrollIntoViewIfNeeded();
  await shotViewport(page, "06_legacy_modules_collapsed");

  await page.evaluate(() => window.scrollTo(0, 0));
  await page.waitForTimeout(300);
  await shotViewport(page, "07_no_strong_colored_bucket_borders");

  try {
    await copyFile(
      path.join(beforeDir, "01_polished_catalog_overview.png"),
      path.join(outDir, "08_before_polish_overview_reference.png"),
    );
    console.log("copied before reference from ui-polish screenshots");
  } catch {
    console.log("before reference not available — skipping copy");
  }

  await browser.close();
  console.log("done");
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
