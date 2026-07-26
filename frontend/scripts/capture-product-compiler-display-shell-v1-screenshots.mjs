/**
 * PRODUCT_COMPILER_DISPLAY_SHELL_V1 — runtime screenshots (labels/IA only).
 * Requires FE :3000 + BE :8000 with Dev Auth.
 */
import { chromium } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.resolve(__dirname, "../../docs/worklog/realignment/audit_assets");
const BASE = process.env.PW_BASE_URL ?? "http://127.0.0.1:3000";

async function shot(page, name) {
  await mkdir(OUT, { recursive: true });
  const file = path.join(OUT, `${name}.png`);
  await page.screenshot({ path: file, fullPage: false });
  console.log("saved", file);
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  await page.goto(`${BASE}/product-system/products`, { waitUntil: "domcontentloaded", timeout: 120_000 });
  await page.getByTestId("product-system-unified-catalog").waitFor({ timeout: 60_000 });
  await shot(page, "21_product_compiler_shell_products_catalog");

  const letters = page.locator(
    `[data-testid="product-system-canonical-catalog-card"][data-template-code="TPL-VOLUMETRIC-LETTERS_v2"]`,
  );
  if ((await letters.count()) > 0) {
    await letters.first().click();
    await page.getByTestId("product-system-template-detail-panel").waitFor({ timeout: 15_000 });
    await shot(page, "21_product_compiler_shell_product_template_detail");
    await page.getByTestId("product-system-template-detail-tab-dossier").click();
    const openEditor = page.getByTestId("product-system-template-detail-open-editor");
    if ((await openEditor.count()) > 0) {
      await openEditor.click();
      await page.waitForTimeout(800);
      const compilerTab = page.getByTestId("product-system-studio-tab-compiler");
      if ((await compilerTab.count()) > 0) {
        await compilerTab.click();
        await page.waitForTimeout(500);
      }
      await shot(page, "21_product_compiler_shell_studio_structure");
    }
  }

  await page.goto(`${BASE}/product-system/components`, { waitUntil: "domcontentloaded", timeout: 120_000 });
  await page.waitForTimeout(1500);
  await shot(page, "21_product_compiler_shell_components");

  await page.goto(`${BASE}/modules`, { waitUntil: "domcontentloaded", timeout: 120_000 });
  await page.waitForTimeout(1500);
  await shot(page, "21_product_compiler_shell_modules_map");

  await page.goto(`${BASE}/execution`, { waitUntil: "domcontentloaded", timeout: 120_000 });
  await page.waitForTimeout(1500);
  await shot(page, "21_product_compiler_shell_execution_plan_states");

  await browser.close();
  console.log("done");
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
