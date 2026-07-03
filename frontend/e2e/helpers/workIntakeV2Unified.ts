import { expect, type Page } from "@playwright/test";

/** Match frontend WORK_INTAKE_V2_AUTOSAVE_MS (700) + buffer for debounced persist. */
export const WORK_INTAKE_V2_AUTOSAVE_MS = 900;

export async function expectUnifiedSaveStatusVisible(page: Page) {
  await expect(page.getByTestId("work-intake-v2-save-status")).toBeVisible();
}

export async function expectNoWizardCheckpointSaveButtons(page: Page) {
  await expect(page.getByTestId("work-intake-v2-save-svg")).toHaveCount(0);
  await expect(page.getByTestId("work-intake-v2-save-production")).toHaveCount(0);
  await expect(page.getByTestId("work-intake-v2-save-lighting")).toHaveCount(0);
}

export async function waitForWorkspacePersistIdle(page: Page, timeout = 20_000) {
  const status = page.getByTestId("work-intake-v2-save-status");
  await expect(status).toBeVisible();
  await page.waitForTimeout(WORK_INTAKE_V2_AUTOSAVE_MS);
  await expect(status).not.toHaveAttribute("data-save-status", "dirty", { timeout });
  await expect(status).not.toHaveAttribute("data-save-status", "saving", { timeout });
}

export async function expectZoneReadinessSummary(page: Page) {
  const summary = page.getByTestId("work-intake-v2-zone-summary");
  await expect(summary).toBeVisible();
  await summary.locator("summary").click();
  await expect(summary.getByText("Detalii job")).toBeVisible();
  await expect(summary.getByText("SVG & layere")).toBeVisible();
  await expect(summary.getByText("Producție / finisaje")).toBeVisible();
  await expect(summary.getByText("Iluminare & surse")).toBeVisible();
  await expect(summary.getByText("Handoff ofertare")).toBeVisible();
}

export async function expectMountingSectionFields(page: Page) {
  const section = page.getByTestId("work-intake-v2-section-mounting");
  await section.scrollIntoViewIfNeeded();
  if (!(await page.getByTestId("work-intake-v2-mounting-system").isVisible())) {
    await section.locator("summary").click();
  }
  await expect(page.getByTestId("work-intake-v2-mounting-system")).toBeVisible();
  await expect(page.getByTestId("work-intake-v2-mounting-template-mode")).toBeVisible();
}

/** Face vinyl controls live inside a collapsed `<details>` section in Zone D. */
export async function revealFaceVinylSection(page: Page) {
  const faceSection = page.getByTestId("work-intake-v2-section-face-vinyl");
  await faceSection.scrollIntoViewIfNeeded();
  const faceWrap = page.getByTestId("work-intake-v2-face-wrap");
  if (!(await faceWrap.isVisible())) {
    await faceSection.locator("summary").click();
  }
  await expect(faceWrap).toBeVisible();
  return faceWrap;
}
