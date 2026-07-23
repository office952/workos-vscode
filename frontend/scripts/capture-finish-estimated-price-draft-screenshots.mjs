import { chromium } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const outDir = path.resolve(
  __dirname,
  "../../docs/qa/screenshots/2026-07-09_finish_estimated_price_draft_v1",
);

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
    "product-system-catalog-bucket-candidate-module-sets",
    "product-system-catalog-bucket-toggle-candidate-module-sets",
  );
  await page.getByTestId("product-system-canonical-filter-deprecated").click();
await page.locator(`[data-testid="product-system-canonical-catalog-card"][data-template-code="TPL-LETTERS-COMPOSER_v1"]`).click();
await page.getByTestId("product-system-template-detail-tab-dossier").click();
await page.getByTestId("product-system-template-detail-open-editor").click();
  await page.waitForSelector('[data-testid="product-system-candidate-module-letters-set"]', { timeout: 15000 });
  await page.getByTestId("product-system-candidate-module-tab-guards-audit").click();
  await page.waitForSelector('[data-testid="product-system-finish-estimate-draft-panel"]', { timeout: 30000 });

  const panel = page.getByTestId("product-system-finish-estimate-draft-panel");

  // 01 — draft status + guards
  await panel.scrollIntoViewIfNeeded();
  await page.getByTestId("product-system-finish-estimate-draft-safety").scrollIntoViewIfNeeded();
  await shot(page, "01_finish_draft_status");

  // 02 — draft rows (Oracal + print/lam)
  await page.getByTestId("product-system-finish-estimate-draft-table").scrollIntoViewIfNeeded();
  await shot(page, "02_finish_draft_rows");

  // 03 — boundaries (excluded keys + safety)
  await page.getByTestId("product-system-finish-estimate-excluded-keys").scrollIntoViewIfNeeded();
  await shot(page, "03_finish_draft_boundaries");

  const text = await panel.innerText();
  const checks = {
    title: /FINISH Estimated Price Draft/i.test(text),
    readonlyInactive: /readonly.*inactive/i.test(text),
    readyForPricingNo: /Ready for pricing:\s*NO/i.test(text),
    pricingActiveZero: /Pricing active rows:\s*0/i.test(text),
    productDefinitionBridgeNo: /ProductDefinition bridge:\s*NO/i.test(text),
    oracal641: /641/i.test(text),
    printLam: /print.*lam/i.test(text),
    returnCantExcluded: /RETURN_CANT_VINYL_APPLICATION_LABOR/i.test(text),
    noActivate: (await page.getByRole("button", { name: /^activate$/i }).count()) === 0,
  };
  console.log("checks", JSON.stringify(checks, null, 2));

  await browser.close();
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
