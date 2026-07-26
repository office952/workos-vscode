/**
 * Nivel 2B evidence screenshots — internal naming cleanup proof.
 * Requires frontend on :3000 with VITE_ENABLE_DEV_AUTH=true.
 */
import { chromium } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const outDir = path.resolve(__dirname, "../../docs/worklog/realignment/audit_assets");
const BASE = "http://127.0.0.1:3000";

async function shot(page, name, { fullPage = false } = {}) {
  const file = path.join(outDir, `${name}.png`);
  await page.screenshot({ path: file, fullPage });
  console.log("saved", file);
}

async function gotoReady(page, url, selector, timeout = 60_000) {
  await page.goto(`${BASE}${url}`, { waitUntil: "networkidle", timeout: 120_000 });
  await page.waitForSelector(selector, { timeout });
  await page.waitForTimeout(500);
}

async function main() {
  await mkdir(outDir, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  // 1) Products catalog (CanonicalCatalog)
  await gotoReady(
    page,
    "/product-system/products",
    '[data-testid="product-system-canonical-catalog-card"]',
  );
  await shot(page, "20_nivel2b_products_catalog");

  // 2) Product Template detail — Letters
  await gotoReady(
    page,
    "/product-system/products/TPL-VOLUMETRIC-LETTERS_v2",
    '[data-testid="product-system-template-detail-panel"]',
  );
  await shot(page, "20_nivel2b_product_template_detail", { fullPage: true });

  // 3) Components / Module produs surface
  await gotoReady(
    page,
    "/product-system/components",
    '[data-testid="product-system-view-components"], [data-testid="product-system-components-tab-panel"], [data-testid="product-system-planned-section"]',
  );
  await shot(page, "20_nivel2b_components");

  // 4) Module chain concepts
  await gotoReady(page, "/modules", '[data-testid="module-chain-page"]');
  await shot(page, "20_nivel2b_modules_concepts", { fullPage: true });

  await browser.close();
  console.log("done");
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
