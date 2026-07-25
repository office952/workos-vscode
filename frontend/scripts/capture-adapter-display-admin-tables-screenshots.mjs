/**
 * ADAPTER_DISPLAY_ADMIN_TABLES_WIRING_V1 — runtime screenshots (labels/IA only).
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
  await page.getByTestId("product-system-unified-catalog").waitFor({ timeout: 60_000 }).catch(() => null);
  await page.waitForTimeout(1200);
  await shot(page, "23_adapter_display_admin_tables_products_catalog");

  const overviewCard = page.getByTestId("product-system-overview-card-components");
  if ((await overviewCard.count()) > 0) {
    await overviewCard.first().scrollIntoViewIfNeeded();
    await shot(page, "23_adapter_display_admin_tables_shared_modules_chrome");
  }

  const letters = page.locator(
    `[data-testid="product-system-canonical-catalog-card"][data-template-code="TPL-VOLUMETRIC-LETTERS_v2"]`,
  );
  if ((await letters.count()) > 0) {
    await letters.first().click();
    await page.getByTestId("product-system-template-detail-panel").waitFor({ timeout: 15_000 });
    await shot(page, "23_adapter_display_admin_tables_product_template_detail");

    const compositionTab = page.getByTestId("product-system-template-detail-tab-composition");
    if ((await compositionTab.count()) > 0) {
      await compositionTab.click();
      await page.waitForTimeout(600);
      await shot(page, "23_adapter_display_admin_tables_composition_list");
    }

    const dossierTab = page.getByTestId("product-system-template-detail-tab-dossier");
    if ((await dossierTab.count()) > 0) {
      await dossierTab.click();
      await page.waitForTimeout(400);
    }
    const openEditor = page.getByTestId("product-system-template-detail-open-editor");
    if ((await openEditor.count()) > 0) {
      await openEditor.click();
      await page.waitForTimeout(1200);
      const field = page.getByTestId("product-system-return-cant-truth-field-component_template_code");
      if ((await field.count()) > 0) {
        await field.first().scrollIntoViewIfNeeded();
        await page.waitForTimeout(300);
        await shot(page, "23_adapter_display_admin_tables_return_cant_module_produs_code");
      } else {
        const ownership = page.getByTestId("product-system-return-cant-truth-container");
        if ((await ownership.count()) > 0) {
          await ownership.first().scrollIntoViewIfNeeded();
          await page.waitForTimeout(300);
          await shot(page, "23_adapter_display_admin_tables_return_cant_field_labels");
        }
      }
    }
  } else {
    await page.goto(`${BASE}/product-system/products/TPL-VOLUMETRIC-LETTERS_v2`, {
      waitUntil: "domcontentloaded",
      timeout: 120_000,
    });
    await page.waitForTimeout(1500);
    await shot(page, "23_adapter_display_admin_tables_product_template_detail");
  }

  await page.goto(`${BASE}/product-system/components`, { waitUntil: "domcontentloaded", timeout: 120_000 });
  await page.waitForTimeout(1200);
  await shot(page, "23_adapter_display_admin_tables_components");

  await page.goto(`${BASE}/modules`, { waitUntil: "domcontentloaded", timeout: 120_000 });
  await page.waitForTimeout(1200);
  await shot(page, "23_adapter_display_admin_tables_modules_map");

  await page.goto(`${BASE}/inventory/pricing`, { waitUntil: "domcontentloaded", timeout: 120_000 });
  await page.waitForTimeout(1200);
  await shot(page, "23_adapter_display_admin_tables_pricing_control");

  await browser.close();
  console.log("done");
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
