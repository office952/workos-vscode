/**
 * Screenshot capture for PRODUCT_SYSTEM_CATALOG_PAGE_CHROME_SLIM_V1
 * Requires frontend dev server on :3000
 */
import { chromium } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const outDir = path.resolve(
  __dirname,
  "../../docs/qa/product-system-catalog-page-chrome-slim-2026-07-09/screenshots",
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
  await page.waitForSelector('[data-testid="product-system-library-header"]', { timeout: 60000 });

  await shotViewport(page, "01_slim_header_and_buckets_high");
  await shotViewport(page, "02_single_line_filter_chips");
  await page.getByTestId("product-system-unified-row-TPL-VOLUMETRIC-LETTERS_v2-action-more").click();
  await page.waitForTimeout(200);
  await shotViewport(page, "03_row_overflow_actions_menu");
  await page.getByTestId("product-system-library-more-menu").click();
  await page.waitForTimeout(200);
  await shotViewport(page, "04_library_more_menu_blueprint");

  await browser.close();
  console.log("done");
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
