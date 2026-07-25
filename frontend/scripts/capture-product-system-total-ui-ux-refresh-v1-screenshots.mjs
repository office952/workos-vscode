/**
 * PRODUCT_SYSTEM_TOTAL_UI_UX_REFRESH_V1 — runtime screenshots.
 * Requires FE :3000 + BE :8000 with Dev Auth. Display / IA recomposition only.
 */
import { chromium } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.resolve(__dirname, "../../docs/worklog/realignment/audit_assets");
const BASE = process.env.PW_BASE_URL ?? "http://127.0.0.1:3000";
const PREFIX = "24_product_system_total_ui_ux_refresh";
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

  // Catalog + spine band + empty-state story
  await page.goto(`${BASE}/product-system/products`, { waitUntil: "domcontentloaded", timeout: 120_000 });
  await page.getByTestId("product-system-unified-catalog").waitFor({ timeout: 60_000 });
  await page.getByTestId("product-system-spine-band").first().waitFor({ timeout: 15_000 });
  await page.waitForTimeout(600);
  await shot(page, "catalog_spine_empty_story");

  // Template detail — product story overview (deep link auto-selects)
  await page.goto(`${BASE}/product-system/products/${LETTERS}`, {
    waitUntil: "domcontentloaded",
    timeout: 120_000,
  });
  await page.getByTestId("product-system-template-detail-panel").waitFor({ timeout: 30_000 });
  await page.getByTestId("product-system-template-story").waitFor({ timeout: 15_000 });
  await page.waitForTimeout(600);
  await shot(page, "template_detail_story");
  await shot(page, "template_detail_story_full", true);

  // Readiness deep section via story button
  const readinessBtn = page.getByTestId("product-system-template-story-open-readiness");
  if ((await readinessBtn.count()) > 0) {
    await readinessBtn.click();
    await page.waitForTimeout(800);
    await shot(page, "template_detail_readiness");
  }

  // Composition deep section
  await page.goto(`${BASE}/product-system/products/${LETTERS}`, {
    waitUntil: "domcontentloaded",
    timeout: 120_000,
  });
  await page.getByTestId("product-system-template-story").waitFor({ timeout: 30_000 });
  const compBtn = page.getByTestId("product-system-template-story-open-composition");
  if ((await compBtn.count()) > 0) {
    await compBtn.click();
    await page.waitForTimeout(800);
    await shot(page, "template_detail_composition");
  }

  // Module produs (planned) + modules map + registry control
  await page.goto(`${BASE}/product-system/components`, { waitUntil: "domcontentloaded", timeout: 120_000 });
  await page.waitForTimeout(1200);
  await shot(page, "components_section");

  await page.goto(`${BASE}/modules`, { waitUntil: "domcontentloaded", timeout: 120_000 });
  await page.waitForTimeout(1500);
  await shot(page, "modules_map");

  await page.goto(`${BASE}/inventory/pricing`, { waitUntil: "domcontentloaded", timeout: 120_000 });
  await page.waitForTimeout(1500);
  await shot(page, "pricing_registry_control");

  await browser.close();
  console.log("done");
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
