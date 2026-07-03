/**
 * WorkIntake V2 → QuoteWizard finish display smoke (BUILD-CI-E2E-WORKINTAKE-TO-QUOTE-FINISH-DISPLAY).
 *
 * Prerequisites:
 *   - Backend :8000 healthy with dev DB
 *   - Fixture seeded: python backend/scripts/seed_commercial_e2e_fixture.py
 *   - Frontend :3000 (playwright webServer or PW_SKIP_WEB_SERVER=1)
 *   - Playwright Chromium: npx playwright install chromium
 */
import { expect, test } from "@playwright/test";
import {
  FIXTURE_FINISH_DISPLAY_INTAKE_CODE,
  probeFinishDisplayLiveDbFixture,
  type FinishDisplayFixtureManifest,
} from "./helpers/commercialFixture";
import {
  expectNoWizardCheckpointSaveButtons,
  expectUnifiedSaveStatusVisible,
  revealFaceVinylSection,
  waitForWorkspacePersistIdle,
} from "./helpers/workIntakeV2Unified";

let fixture: FinishDisplayFixtureManifest | null = null;
let skipReason: string | undefined;

test.describe("WorkIntake V2 → QuoteWizard finish display", () => {
  test.beforeAll(async () => {
    const probe = await probeFinishDisplayLiveDbFixture();
    if (!probe.fixtureAvailable || !probe.manifest) {
      skipReason = probe.reason ?? "Finish-display fixture unavailable";
      return;
    }
    fixture = probe.manifest;
  });

  test.beforeEach(() => {
    test.skip(!fixture, skipReason ?? "Finish-display fixture unavailable");
  });

  test("RAL return + Oracal 8500 face → quote-finish-display", async ({ page }) => {
    test.setTimeout(180_000);

    const intakeCode = fixture!.intake_code ?? FIXTURE_FINISH_DISPLAY_INTAKE_CODE;

    await page.goto(`/intake-v2/${intakeCode}`);
    await page.waitForSelector('[data-testid="work-intake-v2-flow"]', { timeout: 60_000 });

    await expect(page.getByTestId("work-intake-v2-zone-header")).toBeVisible();
    await expect(page.getByTestId("work-intake-v2-zone-job-details")).toBeVisible();
    await expect(page.getByTestId("work-intake-v2-zone-graphics-layers")).toBeVisible();
    await expect(page.getByTestId("work-intake-v2-zone-volumetric-rules")).toBeVisible();
    await expect(page.getByTestId("work-intake-v2-zone-readiness-handoff")).toBeVisible();
    await expect(page.getByTestId("work-intake-v2-stage-nav")).toHaveCount(0);
    await expectUnifiedSaveStatusVisible(page);
    await expectNoWizardCheckpointSaveButtons(page);

    const cta = page.getByTestId("work-intake-v2-open-quote-wizard");

    const zoneD = page.getByTestId("work-intake-v2-zone-volumetric-rules");
    await zoneD.scrollIntoViewIfNeeded();
    await expect(zoneD).toBeVisible();
    await expect(page.getByTestId("work-intake-v2-stage-panel-production")).toBeVisible();
    await expect(page.getByTestId("work-intake-v2-finish-summary")).toBeVisible();

    const faceWrap = await revealFaceVinylSection(page);
    if (!(await faceWrap.isChecked())) {
      await faceWrap.check();
      await waitForWorkspacePersistIdle(page);
    }
    await expect(cta).toBeDisabled();
    await expect(page.getByTestId("work-intake-v2-repair-face-vinyl-code")).toBeVisible();

    const returnFinishSystem = page.getByTestId("work-intake-v2-return-finish-system");
    await returnFinishSystem.scrollIntoViewIfNeeded();
    await returnFinishSystem.selectOption("RAL");
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

    const seriesSelect = page.getByTestId("work-intake-v2-face-vinyl-series");
    await seriesSelect.selectOption("8500");
    await expect(seriesSelect).toHaveValue("8500", { timeout: 10_000 });
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

    await expect(page.getByTestId("work-intake-v2-finish-summary")).toContainText(/8500|010/i);
    await expect(page.getByTestId("work-intake-v2-readiness-status")).toContainText(
      /Gata pentru ofertare/,
      { timeout: 15_000 }
    );
    await expect(page.getByTestId("work-intake-v2-quote-return-finish")).toContainText(
      /9010|RAL/i,
      { timeout: 10_000 }
    );
    await expect(page.getByTestId("work-intake-v2-quote-face-vinyl")).toContainText(
      /8500.*010|010.*8500|translucent/i
    );

    await expect(cta).toBeEnabled({ timeout: 30_000 });

    await cta.click();

    await page.waitForURL(/\/quotes/, { timeout: 30_000 });
    await expect(page.getByText("Cum vrei să calculezi?")).toBeVisible({ timeout: 30_000 });

    const finishDisplay = page.getByTestId("quote-finish-display");
    await expect(finishDisplay).toBeVisible();

    await expect(finishDisplay.getByTestId("quote-finish-display-return-detail")).toContainText(
      /9010/
    );
    await expect(finishDisplay.getByTestId("quote-finish-display-return-approx-note")).toBeVisible();
    await expect(finishDisplay.getByTestId("quote-finish-display-face-label")).toContainText(
      /8500.*translucent|translucent.*8500/i
    );
    await expect(finishDisplay.getByTestId("quote-finish-display-face-detail")).toContainText(
      /8500-010|010/
    );

    await expect(finishDisplay).not.toContainText(/RAL 9005/);
    await expect(finishDisplay.getByTestId("quote-finish-display-return")).toHaveCount(1);
    await expect(finishDisplay.getByTestId("quote-finish-display-face")).toHaveCount(1);
  });
});
