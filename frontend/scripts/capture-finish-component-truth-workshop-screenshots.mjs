import { chromium } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const outDir = path.resolve(__dirname, "../../docs/qa/finish-component-truth-workshop-v1/screenshots");

async function shot(page, name) {
  const file = path.join(outDir, `${name}.png`);
  await page.screenshot({ path: file, fullPage: false });
  console.log("saved", file);
}

async function expandBucket(page, bucketId, toggleId) {
  const bucket = page.getByTestId(bucketId);
  await bucket.scrollIntoViewIfNeeded();
  if ((await bucket.getAttribute("data-expanded")) !== "true") {
    await page.getByTestId(toggleId).click();
    await bucket.waitFor({ state: "visible", timeout: 10000 });
  }
}

async function main() {
  await mkdir(outDir, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto("http://127.0.0.1:3000/product-system", { waitUntil: "networkidle", timeout: 120000 });
  await page.waitForSelector('[data-testid="product-system-unified-catalog"]', { timeout: 60000 });

  await expandBucket(
    page,
    "product-system-catalog-bucket-component-first-sets",
    "product-system-catalog-bucket-toggle-component-first-sets",
  );
  await page.getByTestId("product-system-unified-row-candidate-set").click();
  await page.waitForSelector('[data-testid="product-system-component-first-letters-set"]', { timeout: 15000 });
  await page.getByTestId("product-system-component-first-tab-guards-audit").click();
  await page.waitForSelector('[data-testid="product-system-finish-truth-workshop"]', { timeout: 30000 });

  const workshop = page.getByTestId("product-system-finish-truth-workshop");
  await workshop.scrollIntoViewIfNeeded();
  await shot(page, "01_finish_contract_summary");

  await page.getByTestId("product-system-finish-truth-owns").scrollIntoViewIfNeeded();
  await shot(page, "02_finish_owns_does_not_own");

  await page.getByTestId("product-system-finish-truth-variants-table").scrollIntoViewIfNeeded();
  await shot(page, "03_finish_variants_table");

  await page.getByTestId("product-system-finish-truth-quantity-basis").scrollIntoViewIfNeeded();
  await shot(page, "04_finish_quantity_basis_questions");

  await page.getByTestId("product-system-finish-truth-blockers").scrollIntoViewIfNeeded();
  await shot(page, "05_finish_blockers_and_guards");

  await page.getByTestId("product-system-finish-truth-safety-copy").scrollIntoViewIfNeeded();
  await shot(page, "06_no_dangerous_actions");

  await browser.close();
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
