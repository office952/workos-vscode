import { expect, test } from "@playwright/test";
import {
  INTAKE_V6_THREE_STEP_SMOKE_WORKSPACE_ID,
  assertHeaderStepLabel,
  assertNoRemovedWorkspaceStatusBadge,
  assertThreeStepProgressVisible,
  clickProgressStep,
  gotoIntakeV6Operator,
} from "./helpers/intakeV6ThreeStepSmoke";

test.describe("Intake V6 Step 1 smoke", () => {
  test("full-width layers layout with preview, panel, and continue to configurare", async ({ page }) => {
    await gotoIntakeV6Operator(page, INTAKE_V6_THREE_STEP_SMOKE_WORKSPACE_ID);

    await assertThreeStepProgressVisible(page);
    await clickProgressStep(page, "layers");

    await expect(page.getByTestId("intake-v6-layers-layout")).toBeVisible({ timeout: 30_000 });
    await expect(page.getByTestId("intake-v6-layers-preview-panel")).toBeVisible();
    await expect(page.getByTestId("intake-v6-layers-operator-panel")).toBeVisible();
    await assertNoRemovedWorkspaceStatusBadge(page);

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
      await assertHeaderStepLabel(page, "Configurare");
    }
  });
});
