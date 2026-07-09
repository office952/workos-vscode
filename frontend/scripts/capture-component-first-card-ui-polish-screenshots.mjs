/**
 * Screenshot capture for COMPONENT_FIRST_LETTERS_CARD_UI_POLISH_AND_DRAWER_QA_FIX_V1
 * Requires frontend dev server on :3000
 */
import { chromium } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const outDir = path.resolve(
  __dirname,
  "../../docs/qa/component-first-card-ui-polish-2026-07-09/screenshots",
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

async function waitDrawer(page) {
  await page.getByTestId("product-system-component-first-settings-sheet").waitFor({
    state: "visible",
    timeout: 15000,
  });
  await page.getByTestId("product-system-component-first-readonly-drawer-banner").waitFor({
    state: "visible",
    timeout: 15000,
  });
  await page.waitForTimeout(400);
}

async function shotDrawer(page, name) {
  await waitDrawer(page);
  const file = path.join(outDir, `${name}.png`);
  await page.locator('[data-testid="product-system-component-first-settings-sheet"]').screenshot({ path: file });
  console.log("saved", file);
  await shotViewport(page, `${name}_viewport`);
}

async function main() {
  await mkdir(outDir, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  await page.goto("http://127.0.0.1:3000/product-system", { waitUntil: "networkidle", timeout: 120000 });
  await page.waitForSelector('[data-testid="product-system-component-first-candidate-set-card"]', {
    timeout: 60000,
  });

  await shotPage(page, "01_product_system_top_context");
  await shotViewport(page, "02_candidate_set_card");

  await page.getByTestId("product-system-component-first-view-candidate").click();
  await page.waitForSelector('[data-testid="product-system-component-first-letters-set"]', { timeout: 30000 });
  await shotPage(page, "03_candidate_overview_product_composer_card");

  await page.getByTestId("product-system-component-first-tab-components").click();
  await page.waitForSelector('[data-testid="product-system-component-first-components-list"]', { timeout: 15000 });
  await shotPage(page, "04_components_tab_six_polished_cards");

  await page.getByTestId("product-system-component-first-view-product-settings").click();
  await shotDrawer(page, "05_product_settings_drawer_readonly_banner");

  await page.keyboard.press("Escape");
  await page.waitForTimeout(500);

  await page.getByTestId("product-system-component-first-view-component-settings-TPL-COMP-LETTER-FACE_v1").click();
  await shotDrawer(page, "06_component_settings_face_readonly_banner");

  await page.keyboard.press("Escape");
  await page.waitForTimeout(500);

  await page.getByTestId("product-system-component-first-view-component-settings-TPL-COMP-LETTER-LED_v1").click();
  await shotDrawer(page, "07_component_settings_led_readonly_banner");

  await page.keyboard.press("Escape");
  await page.waitForTimeout(500);

  await page.getByTestId("product-system-component-first-tab-dossier").click();
  await page.waitForSelector('[data-testid="product-system-component-first-dossier-workspace"]', { timeout: 15000 });
  await shotPage(page, "08_dossier_workspace");

  await page.getByTestId("product-system-component-first-tab-components").click();
  await page.getByTestId("product-system-component-first-view-dossier-TPL-COMP-LETTER-FACE_v1").click();
  await page.waitForSelector('[data-testid="product-system-component-first-dossier-card-TPL-COMP-LETTER-FACE_v1"][data-focused="true"]', {
    timeout: 15000,
  });
  await page
    .getByTestId("product-system-component-first-dossier-card-TPL-COMP-LETTER-FACE_v1")
    .scrollIntoViewIfNeeded();
  await page.waitForTimeout(400);
  await shotViewport(page, "09_focused_component_dossier_highlight");

  await page.getByTestId("product-system-component-first-tab-guards-audit").click();
  await page.waitForSelector('[data-testid="product-system-component-first-drift-guard"]', { timeout: 15000 });
  await shotPage(page, "10_guards_audit_tab");

  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await page.waitForTimeout(500);
  await shotPage(page, "11_existing_roots_separated");

  await page.getByTestId("product-system-overview-card-products").click();
  await page.waitForSelector('[data-testid="product-system-template-TPL-VOLUMETRIC-LETTERS_v2"]', {
    timeout: 15000,
  });
  await page.getByTestId("product-system-template-TPL-VOLUMETRIC-LETTERS_v2").scrollIntoViewIfNeeded();
  await page.waitForTimeout(400);
  await page.locator('[data-testid="product-system-template-TPL-VOLUMETRIC-LETTERS_v2"]').screenshot({
    path: path.join(outDir, "12_legacy_tpl_volumetric_letters_v2_full_card.png"),
  });
  console.log("saved", path.join(outDir, "12_legacy_tpl_volumetric_letters_v2_full_card.png"));

  await browser.close();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
