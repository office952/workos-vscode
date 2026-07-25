/**
 * PRODUCT_SYSTEM_BLACK_WORKSPACE_REBUILD_V1 screenshots.
 * "Blank" = structural rebuild from zero — not a dark-theme deliverable.
 * Requires FE :3000 + BE :8000 with Dev Auth.
 */
import { chromium } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.resolve(__dirname, "../../docs/worklog/realignment/audit_assets");
const BASE = process.env.PW_BASE_URL ?? "http://127.0.0.1:3000";
const PREFIX = "26_product_system_blank_workspace";
const LETTERS = "TPL-VOLUMETRIC-LETTERS_v2";

async function shot(page, name, fullPage = false) {
  await mkdir(OUT, { recursive: true });
  const file = path.join(OUT, `${PREFIX}_${name}.png`);
  await page.screenshot({ path: file, fullPage });
  console.log("saved", file);
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 980 } });

  await page.goto(`${BASE}/product-system/products`, {
    waitUntil: "domcontentloaded",
    timeout: 120_000,
  });
  await page.getByTestId("product-system-shell").waitFor({ timeout: 60_000 });
  await page.waitForTimeout(800);
  await shot(page, "products_workspace");

  // Prove planned tabs + pricing chip absent from primary chrome
  const planned = await page.getByTestId("product-system-shell-nav-planned").count();
  const pricingChip = await page.getByTestId("product-system-pricing-registry-link").count();
  console.log("planned_nav_count", planned, "pricing_chip_count", pricingChip);
  await shot(page, "chrome_no_planned_tabs");

  await page.goto(`${BASE}/product-system/products/${LETTERS}`, {
    waitUntil: "domcontentloaded",
    timeout: 120_000,
  });
  await page.getByTestId("product-system-template-detail-panel").waitFor({ timeout: 30_000 });
  await page.getByTestId("product-system-template-story").waitFor({ timeout: 15_000 });
  await page.waitForTimeout(700);
  await shot(page, "letters_center_modules_compiler_readiness");
  await shot(page, "letters_center_full", true);

  // Primary tabs only
  await page.getByTestId("product-system-template-primary-tabs").waitFor({ timeout: 5_000 });
  await shot(page, "primary_tabs_four");

  // Downstream collapsed then open
  const down = page.getByTestId("product-system-template-story-downstream");
  if ((await down.count()) > 0) {
    await shot(page, "downstream_collapsed");
    await down.locator("summary").click();
    await page.waitForTimeout(400);
    await shot(page, "downstream_open");
  }

  // Admin drawer closed / open
  const admin = page.getByTestId("product-system-template-diagnostic-tabs");
  if ((await admin.count()) > 0) {
    await shot(page, "admin_drawer_closed");
    await page.getByTestId("product-system-template-admin-drawer-summary").click();
    await page.waitForTimeout(400);
    await shot(page, "admin_drawer_open");
  }

  // Prove Laboratory Closure not on overview (open publication admin only if needed)
  const labOnOverview = await page.getByTestId("product-system-admin-lab-closure").count();
  console.log("lab_closure_visible_on_default_overview", labOnOverview);
  await shot(page, "overview_no_lab_closure_money");

  await browser.close();
  console.log("done");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
