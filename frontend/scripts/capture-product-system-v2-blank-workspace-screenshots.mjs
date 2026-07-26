/**
 * Capture Product System V2 blank workspace screenshots.
 * Requires FE :3000 (and ideally BE :8000 with auth cookie if needed).
 */
import { chromium } from "playwright";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const outDir = path.resolve(
  __dirname,
  "../../docs/worklog/realignment/audit_assets",
);
const base = process.env.PW_BASE_URL || "http://127.0.0.1:3000";

async function shot(page, name, fullPage = false) {
  const file = path.join(outDir, name);
  await page.screenshot({ path: file, fullPage });
  console.log("wrote", file);
}

async function main() {
  await mkdir(outDir, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 960 } });

  await page.goto(`${base}/product-system/products`, { waitUntil: "networkidle" });
  await page.waitForSelector('[data-testid="product-system-v2-workspace"]', {
    timeout: 30000,
  });
  await shot(page, "27_product_system_v2_blank_products_workspace.png");

  const letters = "TPL-VOLUMETRIC-LETTERS_v2";
  await page.goto(`${base}/product-system/products/${encodeURIComponent(letters)}`, {
    waitUntil: "networkidle",
  });
  await page.waitForSelector('[data-testid="product-system-v2-modules-center"]', {
    timeout: 30000,
  });
  await shot(page, "27_product_system_v2_blank_letters_center.png", true);
  await shot(page, "27_product_system_v2_blank_modules_compiler_readiness.png");

  // Admin closed (default)
  await shot(page, "27_product_system_v2_blank_admin_closed.png");

  // Admin open
  const admin = page.locator('[data-testid="product-system-v2-admin-drawer"]');
  if (await admin.count()) {
    await admin.locator("summary").click();
    await page.waitForSelector('[data-testid="product-system-v2-admin-body"]');
    await shot(page, "27_product_system_v2_blank_admin_open.png", true);
  }

  // Downstream open
  const down = page.locator('[data-testid="product-system-v2-downstream"]');
  if (await down.count()) {
    await down.locator("summary").click();
    await page.waitForSelector('[data-testid="product-system-v2-downstream-channels"]');
    await shot(page, "27_product_system_v2_blank_downstream_open.png");
  }

  // Proof: no dense canonical filter chips on V2 primary
  const filterCount = await page.locator('[data-testid^="product-system-canonical-filter-"]').count();
  console.log("canonical_filter_count_on_v2", filterCount);

  // Legacy isolated still reachable
  await page.goto(`${base}/product-system/products?ps_legacy=1`, {
    waitUntil: "networkidle",
  });
  await page.waitForSelector('[data-testid="product-system-legacy-catalog-badge"]', {
    timeout: 30000,
  });
  await shot(page, "27_product_system_v2_blank_legacy_isolated.png");

  await browser.close();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
