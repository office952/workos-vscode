import { expect, test } from "@playwright/test";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  expectMountingSectionFields,
  expectNoWizardCheckpointSaveButtons,
  expectUnifiedSaveStatusVisible,
  expectZoneReadinessSummary,
  revealFaceVinylSection,
  waitForWorkspacePersistIdle,
} from "./helpers/workIntakeV2Unified";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const FIXTURE_SVG = path.join(__dirname, "fixtures", "lleexxaa.svg");

test("SVG browse button and hidden input parse file", async ({ page }) => {
  test.setTimeout(60_000);

  await page.goto("/intake-v2/WI-E2E-COMMERCIAL-WARN-001");
  await page.waitForSelector('[data-testid="work-intake-v2-flow"]', { timeout: 60_000 });

  await expect(page.getByTestId("work-intake-v2-file-button")).toHaveText(
    "Alege SVG de pe calculator"
  );
  await page.getByTestId("work-intake-v2-file-input").setInputFiles(FIXTURE_SVG);

  await expect(page.getByTestId("work-intake-v2-detected-layers")).toBeVisible({ timeout: 15_000 });
  await expect(page.getByTestId("work-intake-v2-filename-meta")).toHaveValue("lleexxaa.svg");
});

test("WorkIntake V2 volumetric unified operator flow smoke", async ({ page }) => {
  test.setTimeout(180_000);

  await page.goto("/intake-v2/WI-E2E-COMMERCIAL-WARN-001");
  await page.waitForSelector('[data-testid="work-intake-v2-flow"]', { timeout: 60_000 });

  await expect(page.getByText(/WorkIntake V2 — operator volumetric/)).toBeVisible();
  await expect(page.getByTestId("work-intake-v2-stage-nav")).toHaveCount(0);
  await expect(page.getByTestId("work-intake-v2-zone-header")).toBeVisible();
  await expect(page.getByTestId("work-intake-v2-zone-job-details")).toBeVisible();
  await expect(page.getByTestId("work-intake-v2-zone-graphics-layers")).toBeVisible();
  await expect(page.getByTestId("work-intake-v2-zone-volumetric-rules")).toBeVisible();
  await expect(page.getByTestId("work-intake-v2-zone-readiness-handoff")).toBeVisible();

  await expectUnifiedSaveStatusVisible(page);
  await expectNoWizardCheckpointSaveButtons(page);

  const cta = page.getByTestId("work-intake-v2-open-quote-wizard");
  if (await cta.isDisabled()) {
    await expect(page.getByTestId("work-intake-v2-cta-blocker-reason")).toBeVisible();
  }

  await expect(page.getByTestId("work-intake-v2-stage-panel-svg")).toBeVisible();
  await expect(page.getByTestId("work-intake-v2-stage-panel-layers")).toBeVisible();
  await expect(page.getByTestId("work-intake-v2-stage-panel-production")).toBeVisible();
  await expect(page.getByTestId("work-intake-v2-stage-panel-lighting")).toBeVisible();

  const fileInput = page.getByTestId("work-intake-v2-file-input");
  await fileInput.waitFor({ state: "attached", timeout: 30_000 });
  await fileInput.setInputFiles(FIXTURE_SVG);

  await expect(page.getByTestId("work-intake-v2-parse-status")).toBeVisible({ timeout: 15_000 });
  await expect(page.getByTestId("work-intake-v2-stage-panel-svg")).toBeVisible();
  await waitForWorkspacePersistIdle(page);

  await expect(page.getByTestId("work-intake-v2-detected-layers")).toBeVisible({ timeout: 15_000 });

  const confirmLayer = page.getByTestId("work-intake-v2-confirm-letters-layer");
  await expect(confirmLayer).toContainText(/Confirmă layerul/i);
  if (await confirmLayer.isEnabled()) {
    await confirmLayer.click();
    await waitForWorkspacePersistIdle(page);
    await expect(page.getByTestId("work-intake-v2-geometry-panel")).toHaveAttribute(
      "data-geometry-trust",
      /^(current_confirmed|suggested|missing)$/,
      { timeout: 15_000 }
    );
  }

  await expect(page.getByTestId("work-intake-v2-geometry-panel")).toBeVisible();
  const geometryPanel = page.getByTestId("work-intake-v2-geometry-panel");
  const geometryTrust = await geometryPanel.getAttribute("data-geometry-trust");
  const geometryStatus = await geometryPanel.getAttribute("data-geometry-status");
  expect(
    geometryTrust === "current_confirmed" ||
      geometryTrust === "suggested" ||
      geometryTrust === "missing"
  ).toBe(true);

  if (geometryTrust === "current_confirmed") {
    await expect(page.getByTestId("work-intake-v2-geometry-headline")).toContainText(
      /Geometrie confirmată/i
    );
    await expect(page.getByTestId("work-intake-v2-geometry-perimeter")).not.toHaveText(/— m/);
    await expect(page.getByTestId("work-intake-v2-geometry-area")).not.toHaveText(/— m²/);
    await expect(page.getByTestId("work-intake-v2-save-geometry")).toHaveCount(0);
  } else if (geometryTrust === "suggested") {
    await expect(page.getByTestId("work-intake-v2-geometry-headline")).toContainText(/sugerată/i);
  } else if (geometryStatus === "limited") {
    await expect(page.getByTestId("work-intake-v2-geometry-limitation")).toBeVisible();
  }

  await expect(page.getByTestId("work-intake-v2-save-geometry")).toHaveCount(0);

  const ctaBeforeProduction = cta;
  if (await ctaBeforeProduction.isDisabled()) {
    await expect(page.getByTestId("work-intake-v2-cta-blocker-reason")).toContainText(
      /adâncimea cantului|Cant|producție|SVG|layer|iluminare|PSU|folie|față/i
    );
  }

  await page.getByTestId("work-intake-v2-return-depth").selectOption("80");
  await waitForWorkspacePersistIdle(page);

  await expect(page.getByTestId("work-intake-v2-finish-summary")).toBeVisible();
  await expectMountingSectionFields(page);
  await page.getByTestId("work-intake-v2-mounting-system").selectOption("steel_bars");
  await waitForWorkspacePersistIdle(page);
  await expect(page.getByTestId("work-intake-v2-mounting-bar-profile")).toBeVisible();

  let faceWrap = await revealFaceVinylSection(page);
  if (await faceWrap.isChecked()) {
    await faceWrap.uncheck();
    await waitForWorkspacePersistIdle(page);
  }
  faceWrap = await revealFaceVinylSection(page);
  await faceWrap.check();
  await page.getByTestId("work-intake-v2-face-vinyl-series").selectOption("8500");
  await waitForWorkspacePersistIdle(page);
  await expect(cta).toBeDisabled();
  await expect(page.getByTestId("work-intake-v2-repair-face-vinyl-code")).toBeVisible();
  faceWrap = await revealFaceVinylSection(page);
  await faceWrap.uncheck();
  await waitForWorkspacePersistIdle(page);

  await expect(page.getByTestId("work-intake-v2-stage-panel-lighting")).toBeVisible();
  await expect(page.getByTestId("work-intake-v2-lighting-groups")).toHaveCount(0);
  await expect(page.getByTestId("work-intake-v2-add-lighting-group")).toHaveCount(0);

  await page.getByTestId("work-intake-v2-lighting-system").selectOption("led_strip");
  await expect(page.getByTestId("work-intake-v2-led-strip-fields")).toBeVisible();
  await page.getByTestId("work-intake-v2-calc-psu").click();
  await expect(page.getByTestId("work-intake-v2-psu-proposal")).toBeVisible();
  await expect(page.getByTestId("work-intake-v2-psu-proposal-text")).not.toHaveText("—");
  await waitForWorkspacePersistIdle(page);

  await expect(page.getByTestId("work-intake-v2-psu-proposal")).toBeVisible();
  await expectZoneReadinessSummary(page);
  await expect(page.getByTestId("work-intake-v2-quote-preview")).toBeVisible();
  await expect(page.getByTestId("work-intake-v2-quote-psu-summary")).toBeVisible();
  await expect(page.getByTestId("work-intake-v2-quote-psu-summary")).not.toHaveText(
    /— W LED · necesar — W/
  );
  await expect(page.getByTestId("work-intake-v2-quote-lighting-groups")).toHaveCount(0);

  await expect(cta).toBeVisible();
  await expect(cta).toBeEnabled({ timeout: 30_000 });
  await expect(page.getByTestId("work-intake-v2-readiness-status")).toContainText(
    /Gata pentru ofertare/
  );
  await expect(page.getByTestId("work-intake-v2-save-status")).toHaveAttribute(
    "data-save-status",
    /^(saved|needs_confirmation)$/
  );
});
