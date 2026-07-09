/**
 * Screenshot capture for PRODUCT_SYSTEM_IA_SHELL_EXISTING_ROOTS_SEPARATION_V1
 * Requires frontend dev server on :3000
 */
import { chromium } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const outDir = path.resolve(
  __dirname,
  "../../docs/qa/product-system-ia-shell-2026-07-09/screenshots",
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

async function clickPrimaryTab(page, tab) {
  await page.getByTestId(`product-system-primary-tab-${tab}`).click();
  await page.waitForTimeout(400);
}

async function main() {
  await mkdir(outDir, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  await page.goto("http://127.0.0.1:3000/product-system", { waitUntil: "networkidle", timeout: 120000 });
  await page.waitForSelector('[data-testid="product-system-primary-tabs"]', { timeout: 60000 });

  await shotViewport(page, "01_top_summary_and_primary_tabs");
  await shotPage(page, "02_products_tab_existing_roots");

  await clickPrimaryTab(page, "candidate-sets");
  await page.waitForSelector('[data-testid="product-system-component-first-candidate-set-card"]', { timeout: 15000 });
  await shotViewport(page, "03_candidate_sets_collapsed_card");
  await page.getByTestId("product-system-component-first-view-candidate").click();
  await page.waitForSelector('[data-testid="product-system-component-first-letters-set"]', { timeout: 15000 });
  await shotPage(page, "04_candidate_sets_detail_open");

  await clickPrimaryTab(page, "candidate-sets");
  await shotViewport(page, "05_proof_no_existing_roots_under_candidate");

  await clickPrimaryTab(page, "components");
  await page.waitForSelector('[data-testid="product-system-view-components"]', { timeout: 15000 });
  await shotPage(page, "06_components_tab");

  await clickPrimaryTab(page, "dossiers");
  await shotViewport(page, "07_dossiers_tab");

  await clickPrimaryTab(page, "guards-audit");
  await shotViewport(page, "08_guards_audit_tab");

  await clickPrimaryTab(page, "archived");
  await page.waitForSelector('[data-testid="product-system-view-archived"]', { timeout: 15000 });
  await shotPage(page, "09_archived_tab");

  await clickPrimaryTab(page, "products");
  await page.waitForSelector('[data-testid="product-system-existing-roots"]', { timeout: 15000 });
  await page.getByText("TPL-VOLUMETRIC-LETTERS_v2").first().scrollIntoViewIfNeeded();
  await shotViewport(page, "10_tpl_volumetric_letters_v2_in_products_tab");

  await browser.close();
  console.log("done");
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
