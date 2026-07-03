import { expect, test } from "@playwright/test";
import {
  expectMountingSectionFields,
  expectNoWizardCheckpointSaveButtons,
  expectUnifiedSaveStatusVisible,
  revealFaceVinylSection,
  waitForWorkspacePersistIdle,
} from "./helpers/workIntakeV2Unified";

const INTAKE = "/intake-v2/WI-E2E-COMMERCIAL-WARN-001";

test("WorkIntake V2 color registry smoke — RAL return + Oracal 8500 face", async ({
  page,
}) => {
  test.setTimeout(120_000);

  await page.goto(INTAKE);
  await page.waitForSelector('[data-testid="work-intake-v2-flow"]', { timeout: 60_000 });

  await expect(page.getByTestId("work-intake-v2-zone-volumetric-rules")).toBeVisible();
  await expect(page.getByTestId("work-intake-v2-stage-panel-production")).toBeVisible();
  await expectUnifiedSaveStatusVisible(page);
  await expectNoWizardCheckpointSaveButtons(page);
  await expect(page.getByTestId("work-intake-v2-finish-summary")).toBeVisible();
  await expectMountingSectionFields(page);

  await page.getByTestId("work-intake-v2-return-finish-system").selectOption("RAL");
  await expect(page.getByTestId("work-intake-v2-return-ral-select")).toBeVisible();

  await page.getByTestId("work-intake-v2-return-ral-select-search").fill("9010");
  await page.getByTestId("work-intake-v2-return-ral-select-option-RAL-ral-9010").click();
  await expect(page.getByTestId("work-intake-v2-return-ral-select-selected")).toContainText(
    /9010/
  );
  await expect(page.getByTestId("work-intake-v2-return-ral-select-approx-note")).toBeVisible();
  await expect(page.getByTestId("work-intake-v2-finish-summary-return-detail")).toContainText(
    /9010/
  );

  const faceWrap = await revealFaceVinylSection(page);
  if (!(await faceWrap.isChecked())) {
    await faceWrap.check();
    await waitForWorkspacePersistIdle(page);
  }
  await expect(page.getByTestId("work-intake-v2-vinyl-fields")).toBeVisible();
  await expect(page.getByTestId("work-intake-v2-repair-face-vinyl-code")).toBeVisible();

  const seriesSelect = page.getByTestId("work-intake-v2-face-vinyl-series");
  await seriesSelect.selectOption("8500");
  await expect(seriesSelect).toHaveValue("8500", { timeout: 10_000 });
  await expect(page.getByLabel("Culoare Oracal 8500 translucent")).toBeVisible();
  await expect(page.getByTestId("work-intake-v2-face-vinyl-select")).toBeVisible();

  await page.getByTestId("work-intake-v2-face-vinyl-select-search").fill("010");
  await page
    .getByTestId("work-intake-v2-face-vinyl-select-option-ORACAL-8500-010")
    .click({ timeout: 15_000 });
  await expect(page.getByTestId("work-intake-v2-face-vinyl-select-selected")).toContainText(
    /8500|translucent/i
  );
  await page.getByTestId("work-intake-v2-face-vinyl-roll-width").selectOption("1260");
  await waitForWorkspacePersistIdle(page);

  await expect(page.getByTestId("work-intake-v2-finish-summary-face-detail")).toContainText(
    /8500|010/i
  );

  await expect(page.getByTestId("work-intake-v2-quote-return-finish")).toContainText(
    /9010|RAL/i,
    { timeout: 10_000 }
  );
  await expect(page.getByTestId("work-intake-v2-quote-face-vinyl")).toContainText(
    /8500.*010|010.*8500|translucent/i
  );

  const cta = page.getByTestId("work-intake-v2-open-quote-wizard");
  await expect(cta).toBeVisible();
  await expect(page.getByTestId("work-intake-v2-repair-panel")).toBeVisible();
});
