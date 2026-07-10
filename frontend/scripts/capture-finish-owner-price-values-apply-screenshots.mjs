import { chromium } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const outDir = path.resolve(
  __dirname,
  "../../docs/qa/screenshots/2026-07-09_finish_owner_price_values_apply_v1",
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
    "product-system-catalog-bucket-component-first-sets",
    "product-system-catalog-bucket-toggle-component-first-sets",
  );
  await page.getByTestId("product-system-unified-row-candidate-set").click();
  await page.waitForSelector('[data-testid="product-system-component-first-letters-set"]', { timeout: 15000 });
  await page.getByTestId("product-system-component-first-tab-guards-audit").click();
  await page.waitForSelector('[data-testid="product-system-finish-estimate-draft-panel"]', { timeout: 30000 });

  const panel = page.getByTestId("product-system-finish-estimate-draft-panel");
  await panel.scrollIntoViewIfNeeded();

  await page.getByTestId("product-system-finish-estimate-owner-price-values-badge").scrollIntoViewIfNeeded();
  await shot(page, "01_owner_price_values_applied");

  await page.getByTestId("product-system-finish-estimate-labor-evidence").scrollIntoViewIfNeeded();
  await shot(page, "02_labor_evidence_face_vs_wc");

  await page.getByTestId("product-system-finish-estimate-draft-row-artwork_print_only_draft").scrollIntoViewIfNeeded();
  await shot(page, "03_artwork_print_only_blocked");

  const text = await panel.innerText();
  const checks = {
    ownerApplied: /OWNER PRICE VALUES APPLIED/i.test(text),
    faceLabor: /FACE_VINYL_APPLICATION_LABOR/i.test(text),
    wcLegacy: /WC_VINYL_APPLICATION/i.test(text),
    readyNo: /Ready for pricing:\s*NO/i.test(text),
    printOnlyBlocked: /BLOCKED/i.test(text),
    returnCantExcluded: (await page.getByTestId("product-system-finish-estimate-excluded-return_cant_vinyl_labor_excluded").count()) > 0,
  };
  console.log("checks", JSON.stringify(checks, null, 2));

  await browser.close();
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
