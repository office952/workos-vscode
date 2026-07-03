import { expect, test } from "@playwright/test";

const OPERATOR_URL =
  "http://127.0.0.1:3000/intake-v6/22ef834d-f2d0-453b-a7a7-118928c98a39/operator";

test.describe("Intake V6 Step 1 smoke", () => {
  test("full-width layers layout with preview, panel, and continue to review", async ({ page }) => {
    await page.goto(OPERATOR_URL, { waitUntil: "networkidle", timeout: 60_000 });

    await page.getByTestId("intake-v6-progress-step-layers").click();
    await expect(page.getByTestId("intake-v6-layers-layout")).toBeVisible({ timeout: 30_000 });
    await expect(page.getByTestId("intake-v6-layers-preview-panel")).toBeVisible();
    await expect(page.getByTestId("intake-v6-layers-operator-panel")).toBeVisible();
    await expect(page.getByTestId("intake-v6-workspace-status-badge")).toBeVisible();
    await expect(page.getByText("SVG ready")).toHaveCount(0);

    const metrics = page.getByTestId("intake-v6-layers-metrics-strip");
    if (await metrics.isVisible()) {
      await expect(page.getByText("Perimetru vectorial total")).toBeVisible();
    }

    await expect(page.getByTestId("intake-v6-layers-decision-band")).toBeVisible();
    await expect(page.getByTestId("intake-v6-layer-card-grid")).toBeVisible();

    const continueBtn = page.getByTestId("intake-v6-footer-next");
    await expect(continueBtn).toBeVisible();
    if (await continueBtn.isEnabled()) {
      await continueBtn.click();
      await expect(page.getByTestId("intake-v6-header-step")).toHaveText(/Review/i, {
        timeout: 15_000,
      });
    }
  });
});
