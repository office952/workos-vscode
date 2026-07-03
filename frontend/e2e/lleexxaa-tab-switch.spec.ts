import { expect, test } from "@playwright/test";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const LLEEXXAA = "C:\\Users\\offic\\Desktop\\lleexxaa.svg";

test("lleexxaa.svg layers survive tab switch to quote and back", async ({ page }) => {
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

  await expect(page.getByTestId("vector-fast-ask-layer-count")).toContainText("2", {
    timeout: 15_000,
  });

  await page.getByTestId("volumetric-tab-quote").click();
  await expect(page.getByTestId("workspace-quote-panel")).toBeVisible({ timeout: 15_000 });

  await page.getByTestId("volumetric-tab-spec").click();
  await expect(page.getByTestId("workspace-spec-panel")).toBeVisible({ timeout: 15_000 });
  await expect(page.getByTestId("vector-fast-ask-layer-count")).toContainText("2", {
    timeout: 15_000,
  });

  await page.screenshot({
    path: path.join(__dirname, "..", "test-results", "lleexxaa-after-tab-switch.png"),
    fullPage: true,
  });
});
