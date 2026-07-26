/**
 * One-off screenshot capture for CANDIDATE_MODULE_LETTERS_CARD_BASED_UI_RESTRUCTURE_READONLY_V1
 * Run with frontend dev server on :3000 and VITE_ENABLE_DEV_AUTH=true
 */
import { chromium } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const outDir = path.resolve(
  __dirname,
  "../../docs/qa/candidate-module-card-ui-restructure-2026-07-09/screenshots",
);

async function shot(page, name) {
  const file = path.join(outDir, `${name}.png`);
  await page.screenshot({ path: file, fullPage: true });
  console.log("saved", file);
}

async function main() {
  await mkdir(outDir, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  await page.goto("http://127.0.0.1:3000/product-system", { waitUntil: "networkidle", timeout: 120_000 });

  await page.waitForSelector('[data-testid="product-system-candidate-module-candidate-set-card"]', {
    timeout: 60_000,
  });

  await shot(page, "01_product_system_top_context");

  await page.getByTestId("product-system-candidate-module-view-candidate").click();
  await page.waitForSelector('[data-testid="product-system-candidate-module-letters-set"]', { timeout: 30_000 });
  await shot(page, "02_candidate_set_card_and_overview");

  await page.getByTestId("product-system-candidate-module-tab-components").click();
  await page.waitForSelector('[data-testid="product-system-candidate-module-components-list"]', { timeout: 15_000 });
  await shot(page, "03_components_tab_six_cards");

  await page.getByTestId("product-system-candidate-module-view-product-settings").click();
  await page.waitForSelector('[data-testid="product-system-candidate-module-settings-sheet"]', { timeout: 15_000 });
  await shot(page, "04_product_settings_drawer");

  await page.keyboard.press("Escape");
  await page.waitForTimeout(400);

  await page
    .getByTestId("product-system-candidate-module-view-component-settings-TPL-COMP-LETTER-FACE_v1")
    .click();
  await page.waitForSelector('[data-testid="product-system-candidate-module-settings-sheet"]', { timeout: 15_000 });
  await shot(page, "05_component_settings_face");

  await page.keyboard.press("Escape");
  await page.waitForTimeout(400);

  await page.getByTestId("product-system-candidate-module-view-component-settings-TPL-COMP-LETTER-LED_v1").click();
  await page.waitForSelector('[data-testid="product-system-candidate-module-settings-sheet"]', { timeout: 15_000 });
  await shot(page, "06_component_settings_led");

  await page.keyboard.press("Escape");
  await page.waitForTimeout(400);

  await page.getByTestId("product-system-candidate-module-tab-dossier").click();
  await page.waitForSelector('[data-testid="product-system-candidate-module-dossier-workspace"]', { timeout: 15_000 });
  await shot(page, "07_dossier_workspace");

  await page.getByTestId("product-system-candidate-module-dossier-focus-TPL-COMP-LETTER-FACE_v1").click();
  await page.waitForTimeout(600);
  await shot(page, "08_focused_component_dossier_card");

  await page.getByTestId("product-system-candidate-module-tab-guards-audit").click();
  await page.waitForSelector('[data-testid="product-system-candidate-module-drift-guard"]', { timeout: 15_000 });
  await shot(page, "09_guards_audit_tab");

  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await page.waitForTimeout(500);
  await shot(page, "10_existing_roots_separated");

  await browser.close();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
