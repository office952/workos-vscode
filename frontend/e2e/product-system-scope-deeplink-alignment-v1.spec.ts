import { expect, test, type Page } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const QA_DIR = path.resolve(
  __dirname,
  "../../docs/qa/product-system-scope-deeplink-alignment-v1/screenshots",
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

test.describe("Product System scope and deep-link alignment v1", () => {
  test("honors template query, archived state, and browser history", async ({ page }) => {
    await page.goto(`/product-system?template=${encodeURIComponent(LETTERS)}`, {
      waitUntil: "domcontentloaded",
      timeout: 120_000,
    });
    await expect(page.getByTestId("product-system-unified-catalog")).toBeVisible({ timeout: 60_000 });
    await expect.poll(async () => displayedTemplateCode(page)).toBe(LETTERS);
    expect(page.url()).toMatch(/product-system\/products/);
    await saveScreenshot(page, "01_letters_deeplink_exact");

    await page.goto(`/product-system?template=${encodeURIComponent(ACM)}`, {
      waitUntil: "domcontentloaded",
      timeout: 120_000,
    });
    await expect(page.getByTestId("product-system-unified-catalog")).toBeVisible({ timeout: 60_000 });
    await expect.poll(async () => displayedTemplateCode(page)).toBe(ACM);
    expect(page.url()).toMatch(/product-system\/products/);
    await saveScreenshot(page, "02_acm_deeplink_exact");

    await page.goto(`/product-system?template=${encodeURIComponent(LOGO)}`, {
      waitUntil: "domcontentloaded",
      timeout: 120_000,
    });
    await expect(page.getByTestId("product-system-template-query-unavailable")).toBeVisible({
      timeout: 30_000,
    });
    await expect(page.getByTestId("product-system-template-query-unavailable")).toContainText(
      /Template indisponibil sau inexistent/i,
    );
    await expect(page.getByTestId("product-system-template-detail-panel")).toHaveCount(0);
    await saveScreenshot(page, "03_archived_template_explicit_state");

    await page.goto(`/product-system?template=${encodeURIComponent(ACM)}`, {
      waitUntil: "domcontentloaded",
      timeout: 120_000,
    });
    await expect.poll(async () => displayedTemplateCode(page)).toBe(ACM);
    await page.reload({ waitUntil: "domcontentloaded" });
    await expect.poll(async () => displayedTemplateCode(page)).toBe(ACM);
    expect(page.url()).toMatch(/product-system\/products/);

    await page.goto(`/product-system?template=${encodeURIComponent(LETTERS)}`, {
      waitUntil: "domcontentloaded",
      timeout: 120_000,
    });
    await expect.poll(async () => displayedTemplateCode(page)).toBe(LETTERS);
    await page.goBack({ waitUntil: "domcontentloaded" });
    await expect.poll(async () => displayedTemplateCode(page)).toBe(ACM);
    await page.goForward({ waitUntil: "domcontentloaded" });
    await expect.poll(async () => displayedTemplateCode(page)).toBe(LETTERS);
    await saveScreenshot(page, "04_history_refresh_preserved");

    await page.goto("/product-system?template=TPL-DOES-NOT-EXIST", {
      waitUntil: "domcontentloaded",
      timeout: 120_000,
    });
    await expect(page.getByTestId("product-system-template-query-unavailable")).toBeVisible({
      timeout: 30_000,
    });
    await expect(page.getByTestId("product-system-template-detail-panel")).toHaveCount(0);
  });
});
