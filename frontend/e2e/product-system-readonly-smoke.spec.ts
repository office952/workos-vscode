import { expect, test, type Page } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const QA_SCREENSHOTS = path.resolve(
  process.cwd(),
  "../docs/qa/product-system-playwright-readonly-smoke-v1/screenshots",
);

const BUCKET = {
  currentProducts: "product-system-catalog-bucket-current-products",
  candidateProducts: "product-system-catalog-bucket-candidate-products",
  componentFirstSets: "product-system-catalog-bucket-component-first-sets",
  legacyModules: "product-system-catalog-bucket-legacy-shared-modules",
  archived: "product-system-catalog-bucket-archived",
} as const;

const BUCKET_TOGGLE = {
  currentProducts: "product-system-catalog-bucket-toggle-current-products",
  candidateProducts: "product-system-catalog-bucket-toggle-candidate-products",
  componentFirstSets: "product-system-catalog-bucket-toggle-component-first-sets",
  legacyModules: "product-system-catalog-bucket-toggle-legacy-shared-modules",
  archived: "product-system-catalog-bucket-toggle-archived",
} as const;

const COMPONENT_TEMPLATE_CODES = [
  "TPL-COMP-LETTER-FACE_v1",
  "TPL-COMP-LETTER-BACK_v1",
  "TPL-COMP-LETTER-RETURN-CANT_v1",
  "TPL-COMP-LETTER-LED_v1",
  "TPL-COMP-LETTER-FINISH_v1",
  "TPL-COMP-LETTER-MOUNTING_v1",
] as const;

async function saveScreenshot(page: Page, name: string) {
  await mkdir(QA_SCREENSHOTS, { recursive: true });
  await page.screenshot({
    path: path.join(QA_SCREENSHOTS, `${name}.png`),
    fullPage: false,
  });
}

async function expandBucketIfNeeded(page: Page, bucketTestId: string, toggleTestId: string) {
  const bucket = page.getByTestId(bucketTestId);
  await expect(bucket).toBeVisible({ timeout: 30_000 });
  if ((await bucket.getAttribute("data-expanded")) !== "true") {
    await page.getByTestId(toggleTestId).click();
    await expect(bucket).toHaveAttribute("data-expanded", "true", { timeout: 10_000 });
  }
}

async function assertNoDangerousActions(page: Page) {
  const dangerousPatterns = [
    /^activate$/i,
    /^promote$/i,
    /create quote/i,
    /expose to work intake/i,
    /make offerable/i,
    /activate logo/i,
    /seed live/i,
    /write product truth/i,
  ];

  for (const pattern of dangerousPatterns) {
    await expect(page.getByRole("button", { name: pattern })).toHaveCount(0);
  }

  const pageText = (await page.locator("body").innerText()).toLowerCase();
  expect(pageText).not.toMatch(/\bwi=true\b/);
  expect(pageText).not.toMatch(/\bpricing=true\b/);
  expect(pageText).not.toMatch(/\bpd=true\b/);
}

test.describe("Product System readonly smoke", () => {
  test("catalog buckets, lifecycle labels, and guardrails stay operator-safe", async ({ page }) => {
    await page.goto("/product-system", { waitUntil: "domcontentloaded", timeout: 120_000 });
    await expect(page.getByTestId("product-system-unified-catalog")).toBeVisible({ timeout: 60_000 });
    await expect(page.getByRole("heading", { name: /Product System/i })).toBeVisible();
    await expect(page.getByTestId("product-system-catalog-overview")).toBeVisible();
    await expect(page.locator('[data-testid="product-system-unified-catalog"]')).not.toHaveText(
      /something went wrong|error boundary/i,
    );

    await saveScreenshot(page, "01_product_system_loaded");

    await expect(page.getByTestId(BUCKET.currentProducts)).toBeVisible();
    await expect(page.getByTestId(BUCKET.candidateProducts)).toBeVisible();
    await expect(page.getByTestId(BUCKET.componentFirstSets)).toBeVisible();
    await expect(page.getByTestId(BUCKET.legacyModules)).toBeVisible();

    const archivedBucket = page.getByTestId(BUCKET.archived);
    if ((await archivedBucket.count()) > 0) {
      await expect(archivedBucket).toBeVisible();
    }

    const lettersRow = page.getByTestId("product-system-unified-row-TPL-VOLUMETRIC-LETTERS_v2");
    await expect(lettersRow).toBeVisible({ timeout: 30_000 });
    await expect(lettersRow).toHaveText(/Current active root/i);
    await expect(lettersRow).toHaveText(/Used today/i);
    await expect(lettersRow).toHaveText(/Offerable/i);
    await expect(lettersRow).toHaveText(/Work Intake:\s*yes/i);

    await lettersRow.click();
    await expect(page.getByTestId("product-system-template-detail-panel")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("product-system-template-detail-bucket-headline")).toHaveText(
      /Rădăcină activă|folosită azi/i,
    );
    await expect(page.getByTestId("product-system-template-detail-overview")).toHaveText(/Work Intake/i);
    await expect(page.getByTestId("product-system-template-detail-overview")).toHaveText(/offerable/i);

    await saveScreenshot(page, "02_active_root_assertions_visible");

    await expandBucketIfNeeded(page, BUCKET.candidateProducts, BUCKET_TOGGLE.candidateProducts);
    const logoRow = page.getByTestId("product-system-unified-row-TPL-VOLUMETRIC-LOGO_v1");
    await expect(logoRow).toBeVisible({ timeout: 15_000 });
    await expect(logoRow).toHaveText(/Candidate product/i);
    await expect(logoRow).toHaveText(/Not Work Intake/i);
    await expect(logoRow).toHaveText(/Owner GO/i);
    await expect(logoRow).not.toHaveText(/Offerable/i);
    await expect(logoRow).not.toHaveText(/Work Intake:\s*yes/i);

    await logoRow.click();
    await expect(page.getByTestId("product-system-template-detail-bucket-headline")).toHaveText(
      /candidate|fără Work Intake|fară Work Intake/i,
    );
    await expect(page.getByTestId("product-system-template-detail-overview")).not.toHaveText(/Work Intake DA/i);

    await saveScreenshot(page, "03_logo_candidate_safe");

    await expandBucketIfNeeded(page, BUCKET.componentFirstSets, BUCKET_TOGGLE.componentFirstSets);
    await page.getByTestId("product-system-unified-row-candidate-set").click();
    await expect(page.getByTestId("product-system-component-first-letters-set")).toBeVisible({
      timeout: 15_000,
    });

    const componentFirstPanel = page.getByTestId("product-system-component-first-letters-set");
    await expect(componentFirstPanel).toHaveText(/Component-first|component-first/i);
    await expect(componentFirstPanel).toHaveText(/Product Composer|Composer/i);
    await expect(componentFirstPanel).toHaveText(/Readonly|READONLY/i);
    await expect(componentFirstPanel).toHaveText(/NOT OFFERABLE|Not offerable/i);
    await expect(page.getByTestId("product-system-component-first-completeness-count")).toHaveText(
      /Live rows:\s*0\/7/i,
    );
    await expect(page.getByTestId("product-system-component-first-dossier-contract-summary")).toHaveText(
      /Dossier contract:\s*7\/7/i,
    );

    await page.getByTestId("product-system-component-first-tab-components").click();
    const componentsTable = page.getByTestId("product-system-component-first-components-table");
    await expect(componentsTable).toBeVisible({ timeout: 10_000 });
    for (const templateCode of COMPONENT_TEMPLATE_CODES) {
      await expect(componentsTable).toContainText(templateCode);
    }

    await page.getByTestId("product-system-component-first-tab-guards-audit").click();
    const guardLabels = page.getByTestId("product-system-component-first-inert-guard-labels");
    await expect(guardLabels).toBeVisible({ timeout: 10_000 });
    await expect(guardLabels).toHaveText(/Work Intake exposure:\s*blocked/i);
    await expect(guardLabels).toHaveText(/Pricing activation:\s*blocked/i);
    await expect(guardLabels).toHaveText(/ProductDefinition runtime:\s*blocked/i);
    await expect(guardLabels).toHaveText(/ProductAggregate runtime:\s*blocked/i);
    await expect(guardLabels).toHaveText(/Quote\/Order\/Execution:\s*blocked/i);

    const workshop = page.getByTestId("product-system-truth-owner-workshop");
    await expect(workshop).toBeVisible({ timeout: 10_000 });
    await expect(page.getByTestId("product-system-truth-workshop-global-status")).toHaveText(
      /OWNER INPUT REQUIRED/i,
    );
    await expect(workshop).toHaveText(/RETURN-CANT/i);
    await expect(workshop).toHaveText(/Culoare Stock/i);
    await expect(workshop).toHaveText(/Oracal/i);
    await expect(workshop).toHaveText(/Vopsit RAL/i);
    await expect(workshop).toHaveText(/No Product Truth write/i);
    await expect(workshop).toHaveText(/No Pricing activation/i);
    await expect(workshop).toHaveText(/No Work Intake exposure/i);
    await expect(workshop).toHaveText(/Întrebări pentru owner/i);
    await expect(page.getByRole("button", { name: /^save$/i })).toHaveCount(0);
    await expect(page.getByRole("button", { name: /write product truth/i })).toHaveCount(0);

    await saveScreenshot(page, "04_component_first_guards_blocked");

    const legacyBucket = page.getByTestId(BUCKET.legacyModules);
    await legacyBucket.scrollIntoViewIfNeeded();
    await expect(legacyBucket).toHaveAttribute("data-expanded", "false");

    await expandBucketIfNeeded(page, BUCKET.legacyModules, BUCKET_TOGGLE.legacyModules);
    const legacyRow = page.getByTestId("product-system-unified-row-TPL-VOLUMETRIC-FACE_v1");
    await expect(legacyRow).toBeVisible({ timeout: 15_000 });
    await expect(legacyRow).toHaveText(/Legacy internal module/i);
    await expect(legacyRow).toHaveText(/Used by parent product/i);
    await expect(page.getByTestId("product-system-unified-row-TPL-COMP-LETTER-FACE_v1")).toHaveCount(0);

    await page.evaluate(() => window.scrollTo(0, 0));
    await page.getByTestId(BUCKET_TOGGLE.legacyModules).click();
    await expect(legacyBucket).toHaveAttribute("data-expanded", "false", { timeout: 10_000 });

    await saveScreenshot(page, "05_legacy_collapsed");

    await expandBucketIfNeeded(page, BUCKET.legacyModules, BUCKET_TOGGLE.legacyModules);
    await expect(page.getByTestId("product-system-legacy-bucket-support-copy")).toHaveText(
      /Legacy support only/i,
    );
    await page.getByTestId("product-system-legacy-bucket-view-replacement-map").click();
    await expect(page.getByTestId("product-system-legacy-replacement-readiness")).toBeVisible({
      timeout: 15_000,
    });
    await expect(page.getByTestId("product-system-legacy-replacement-global-verdict")).toHaveText(
      /NOT READY FOR DELETE/i,
    );
    await expect(page.getByTestId("product-system-legacy-replacement-summary-delete-ready-count")).toHaveText("0");
    const replacementTable = page.getByTestId("product-system-legacy-replacement-table");
    await expect(replacementTable).toContainText("TPL-VOLUMETRIC-FACE_v1");
    await expect(replacementTable).toContainText("TPL-COMP-LETTER-FACE_v1");
    await expect(replacementTable).toContainText("TPL-VOLUMETRIC-LED_v1");
    await expect(replacementTable).toContainText("TPL-COMP-LETTER-LED_v1");
    await expect(replacementTable).toContainText("TPL-VOLUM-ALUMINIU_v1");
    await expect(replacementTable).toContainText("TPL-COMP-LETTER-RETURN-CANT_v1");

    await saveScreenshot(page, "06_legacy_replacement_readiness");

    await expandBucketIfNeeded(page, BUCKET.componentFirstSets, BUCKET_TOGGLE.componentFirstSets);
    await page.getByTestId("product-system-unified-row-candidate-set").click();
    await expect(page.getByTestId("product-system-component-first-replacement-context")).toBeVisible({
      timeout: 15_000,
    });
    await expect(page.getByTestId("product-system-component-first-replacement-context")).toHaveText(
      /Nu înlocuiește runtime acum|replacement map readonly/i,
    );
    await expect(page.getByTestId("product-system-component-first-replaces-face")).toBeVisible();

    await saveScreenshot(page, "07_component_first_replacement_context");

    const pageText = (await page.locator("body").innerText()).toLowerCase();
    expect(pageText).not.toMatch(/ready to delete/);
    await expect(page.getByRole("button", { name: /^delete now$/i })).toHaveCount(0);

    await assertNoDangerousActions(page);
  });
});
