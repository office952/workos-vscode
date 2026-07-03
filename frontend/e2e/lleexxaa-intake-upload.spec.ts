import { expect, test } from "@playwright/test";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
/** Same bytes as repo fixture; loaded from user Desktop for real-world proof. */
const LLEEXXAA = "C:\\Users\\offic\\Desktop\\lleexxaa.svg";

test("lleexxaa.svg upload shows parsed layers on volumetric intake", async ({ page }) => {
  test.setTimeout(120_000);

  await page.goto("/intake/WI-E2E-COMMERCIAL-WARN-001");
  await page.waitForSelector('[data-testid="volumetric-intake-page"]', { timeout: 60_000 });

  const vectorPathway = page.getByTestId("intake-pathway-vector");
  if (await vectorPathway.isVisible()) {
    await vectorPathway.click();
  }

  const fileInput = page.getByTestId("vector-fast-ask-file-input");
  await fileInput.waitFor({ state: "attached", timeout: 30_000 });
  await fileInput.setInputFiles(LLEEXXAA);

  await expect(page.getByTestId("vector-parse-status-banner")).toBeVisible({ timeout: 15_000 });
  await expect(page.getByTestId("vector-parse-file-facts")).toContainText("lleexxaa.svg");
  await expect(page.getByTestId("vector-fast-ask-layer-count")).toContainText("2 layere", {
    timeout: 15_000,
  });
  await expect(page.getByTestId("vector-primary-letters-layer-section")).toBeVisible();

  const confirmBtn = page.getByTestId("vector-confirm-letters-layer");
  if (await confirmBtn.isEnabled()) {
    await confirmBtn.click();
  }
  await expect(page.getByTestId("vector-letters-layer-confirmed")).toBeVisible({ timeout: 15_000 });

  await page.screenshot({
    path: path.join(__dirname, "..", "test-results", "lleexxaa-intake-parsed.png"),
    fullPage: true,
  });

  await page.getByTestId("volumetric-tab-quote").click();
  await page.waitForSelector('[data-testid="quote-handoff-panel"]', { timeout: 30_000 }).catch(() => undefined);
  await page.screenshot({
    path: path.join(__dirname, "..", "test-results", "lleexxaa-intake-quote-tab.png"),
    fullPage: true,
  });
});
