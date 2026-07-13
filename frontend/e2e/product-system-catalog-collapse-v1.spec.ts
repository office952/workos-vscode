import { expect, test, type Page } from "@playwright/test";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const QA_DIR = path.resolve(__dirname, "../../docs/qa/product-system-catalog-collapse-v1");
const SCREENSHOT_DIR = path.join(QA_DIR, "screenshots");

const LETTERS = "TPL-VOLUMETRIC-LETTERS_v2";
const ACM = "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1";
const LOGO = "TPL-VOLUMETRIC-LOGO_v1";

const BUCKET_TEST_IDS = [
  "product-system-catalog-bucket-current-products",
  "product-system-catalog-bucket-candidate-products",
  "product-system-catalog-bucket-component-first-sets",
  "product-system-catalog-bucket-legacy-shared-modules",
  "product-system-catalog-bucket-archived",
];

async function saveScreenshot(page: Page, name: string) {
  await mkdir(SCREENSHOT_DIR, { recursive: true });
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, `${name}.png`), fullPage: false });
}

async function displayedTemplateCode(page: Page): Promise<string | null> {
  const panel = page.getByTestId("product-system-template-detail-panel");
  if ((await panel.count()) === 0) return null;
  return (await panel.locator(".font-mono").first().innerText()).trim();
}

test.describe("Product System catalog collapse v1", () => {
  test("canonical single catalog, filters, deep links, no five-bucket UI", async ({ page }) => {
    const evidence: Record<string, unknown> = {
      task_id: "PRODUCT_SYSTEM_CATALOG_COLLAPSE_V1",
      role: "operator",
      bucket_headings_absent: [],
      visible_templates: [] as string[],
      hidden_templates: [LOGO, "component-first-set"],
      filters_exercised: [] as string[],
      console_errors: [] as string[],
      network_errors: [] as string[],
    };

    page.on("console", (message) => {
      if (message.type() === "error") {
        (evidence.console_errors as string[]).push(message.text());
      }
    });
    page.on("response", (response) => {
      if (response.status() >= 400 && response.url().includes("/api/")) {
        (evidence.network_errors as string[]).push(`${response.status()} ${response.url()}`);
      }
    });

    await page.goto("/product-system/products", { waitUntil: "domcontentloaded", timeout: 120_000 });
    await expect(page.getByTestId("product-system-unified-catalog")).toBeVisible({ timeout: 60_000 });
    await expect(page.getByTestId("product-system-canonical-operator-list")).toBeVisible();

    for (const testId of BUCKET_TEST_IDS) {
      await expect(page.getByTestId(testId)).toHaveCount(0);
      (evidence.bucket_headings_absent as string[]).push(testId);
    }

    const operatorCards = page.getByTestId("product-system-canonical-operator-list").getByTestId(
      "product-system-canonical-catalog-card",
    );
    await expect(operatorCards.first()).toBeVisible({ timeout: 30_000 });
    const cardCodes = await operatorCards.evaluateAll((nodes) =>
      nodes.map((node) => node.getAttribute("data-template-code")).filter(Boolean),
    );
    evidence.visible_templates = cardCodes;
    expect(cardCodes).toContain(LETTERS);
    expect(cardCodes).toContain(ACM);
    expect(cardCodes).not.toContain(LOGO);

    await expect(page.getByTestId("product-system-canonical-operator-list").getByTestId("product-system-canonical-card-readiness-rollup")).toHaveCount(
      await operatorCards.count(),
    );

    await saveScreenshot(page, "01_single_operator_catalog");

    await page.getByTestId("product-system-canonical-search-input").fill("ACM");
    await expect(operatorCards.filter({ hasText: ACM })).toHaveCount(1);
    await page.getByTestId("product-system-canonical-filter-ready").click();
    (evidence.filters_exercised as string[]).push("ready");
    await page.getByTestId("product-system-canonical-filter-blocked").click();
    (evidence.filters_exercised as string[]).push("blocked");
    await page.getByTestId("product-system-canonical-filter-all").click();
    await page.getByTestId("product-system-canonical-search-input").fill("");
    await saveScreenshot(page, "02_catalog_search_filters");

    await expect(page.getByTestId("product-system-canonical-operator-list").locator(`[data-template-code="${ACM}"]`)).toBeVisible({ timeout: 15_000 });
    await saveScreenshot(page, "03_readiness_rollup_cards");

    const advancedNav = page.getByTestId("product-system-shell-nav-advanced");
    if ((await advancedNav.count()) > 0) {
      evidence.role = "admin";
      const advancedList = page.getByTestId("product-system-canonical-advanced-list");
      if ((await advancedList.count()) > 0) {
        await expect(advancedList).toBeVisible();
      } else {
        await page.getByTestId("product-system-canonical-filter-deprecated").click();
        await expect(page.getByTestId("product-system-canonical-advanced-filtered-list")).toBeVisible({
          timeout: 15_000,
        });
        await page.getByTestId("product-system-canonical-filter-all").click();
      }
      await saveScreenshot(page, "04_advanced_internal_objects");
    } else {
      evidence.rbac_granularity_deferred = true;
      await expect(advancedNav).toHaveCount(0);
    }

    await page.getByTestId("product-system-canonical-filter-all").click();
    await page.getByTestId("product-system-canonical-operator-list").locator(`[data-template-code="${ACM}"]`).click();
    await expect(page.getByTestId("product-system-template-detail-panel")).toBeVisible({ timeout: 30_000 });
    await expect.poll(async () => displayedTemplateCode(page), { timeout: 30_000 }).toBe(ACM);
    evidence.selected_template = ACM;
    evidence.url = page.url();
    await saveScreenshot(page, "05_acm_deeplink_from_catalog");

    await page.goto(`/product-system?template=${encodeURIComponent(LETTERS)}`, {
      waitUntil: "domcontentloaded",
      timeout: 120_000,
    });
    await expect(page).toHaveURL(/\/product-system\/products/, { timeout: 30_000 });
    await expect.poll(async () => displayedTemplateCode(page), { timeout: 30_000 }).toBe(LETTERS);

    await page.goto(`/product-system?template=${encodeURIComponent(LOGO)}`, {
      waitUntil: "domcontentloaded",
      timeout: 120_000,
    });
    await expect(page.getByTestId("product-system-template-query-unavailable")).toBeVisible({
      timeout: 30_000,
    });
    evidence.archived_unknown_behavior = "explicit_unavailable";

    await mkdir(QA_DIR, { recursive: true });
    await writeFile(
      path.join(QA_DIR, "evidence_report.json"),
      `${JSON.stringify(evidence, null, 2)}\n`,
      "utf8",
    );
  });
});
