import { expect, test, type Page } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const QA_DIR = path.resolve(
  __dirname,
  "../../docs/qa/product-system-ui-shell-navigation-v1/screenshots",
);

const LETTERS = "TPL-VOLUMETRIC-LETTERS_v2";
const ACM = "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1";
const LOGO = "TPL-VOLUMETRIC-LOGO_v1";

async function saveScreenshot(page: Page, name: string) {
  await mkdir(QA_DIR, { recursive: true });
  await page.screenshot({ path: path.join(QA_DIR, `${name}.png`), fullPage: false });
}

async function displayedTemplateCode(page: Page): Promise<string | null> {
  const panel = page.getByTestId("product-system-template-detail-panel");
  if ((await panel.count()) === 0) return null;
  return (await panel.locator(".font-mono").first().innerText()).trim();
}

test.describe("Product System UI shell and navigation v1", () => {
  test("canonical shell, routes, deep links, and pricing link", async ({ page }) => {
    await page.goto("/product-system", { waitUntil: "domcontentloaded", timeout: 120_000 });
    await expect(page).toHaveURL(/\/product-system\/products(?:\?|$|\/)/, { timeout: 30_000 });
    await expect(page.getByTestId("product-system-shell")).toBeVisible({ timeout: 60_000 });
    await expect(page.getByTestId("product-system-shell-nav-products")).toBeVisible();
    await saveScreenshot(page, "01_operator_products_shell");

    await expect(page.getByTestId("product-system-shell-nav")).toBeVisible();
    await expect(page.getByTestId("product-system-shell-nav-validation")).toBeVisible();
    await saveScreenshot(page, "02_canonical_navigation");

    await page.goto(
      `/product-system/products/${encodeURIComponent(LETTERS)}`,
      { waitUntil: "domcontentloaded", timeout: 120_000 },
    );
    await expect(page.getByTestId("product-system-unified-catalog")).toBeVisible({ timeout: 60_000 });
    await expect.poll(async () => displayedTemplateCode(page)).toBe(LETTERS);
    await expect(page.getByTestId("product-system-products-page")).toHaveAttribute(
      "data-canonical-template-code",
      LETTERS,
    );
    await saveScreenshot(page, "03_product_detail_canonical_route");

    const advancedNav = page.getByTestId("product-system-shell-nav-advanced");
    if ((await advancedNav.count()) > 0) {
      await advancedNav.click();
      await expect(page.getByTestId("product-system-planned-section")).toBeVisible();
    } else {
      await expect(advancedNav).toHaveCount(0);
    }
    await saveScreenshot(page, "04_advanced_visibility_or_deferred");

    await page.goto("/product-system/products", { waitUntil: "domcontentloaded", timeout: 120_000 });
    await page.getByTestId("product-system-pricing-registry-link").click();
    await expect(page).toHaveURL(/\/inventory\/pricing/, { timeout: 30_000 });
    await saveScreenshot(page, "05_pricing_registry_deeplink");

    await page.goto(`/product-system?template=${encodeURIComponent(ACM)}`, {
      waitUntil: "domcontentloaded",
      timeout: 120_000,
    });
    await expect(page.getByTestId("product-system-unified-catalog")).toBeVisible({ timeout: 60_000 });
    await expect.poll(async () => displayedTemplateCode(page)).toBe(ACM);

    await page.goto(`/product-system?template=${encodeURIComponent(LOGO)}`, {
      waitUntil: "domcontentloaded",
      timeout: 120_000,
    });
    await expect(page.getByTestId("product-system-template-query-unavailable")).toBeVisible({
      timeout: 30_000,
    });
    await expect(page.getByTestId("product-system-template-detail-panel")).toHaveCount(0);

    await page.goto("/product-system/components", { waitUntil: "domcontentloaded", timeout: 120_000 });
    await expect(page.getByTestId("product-system-planned-section")).toContainText(
      /Această secțiune va fi activată/i,
    );
  });
});
