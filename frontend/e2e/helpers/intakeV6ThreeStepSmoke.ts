import { expect, type Page } from "@playwright/test";

/** Audit fixture — IV6-189D2F12, cant 60 mm, print_laminate, real artwork blocker. */
export const INTAKE_V6_THREE_STEP_SMOKE_WORKSPACE_ID = "22ef834d-f2d0-453b-a7a7-118928c98a39";

/** Runtime capture read-model fixture (Configurare step). */
export const INTAKE_V6_RUNTIME_CAPTURE_WORKSPACE_ID = "668ffeb2-5d2b-4eb6-a5c4-1a4618c6de7c";

export const INTAKE_V6_VISIBLE_STEP_LABELS = ["Straturi", "Configurare", "Confirmare"] as const;

export function intakeV6OperatorUrl(workspaceId: string): string {
  return `http://127.0.0.1:3000/intake-v6/${workspaceId}/operator`;
}

export async function gotoIntakeV6Operator(page: Page, workspaceId: string): Promise<void> {
  await page.goto(intakeV6OperatorUrl(workspaceId), { waitUntil: "networkidle", timeout: 120_000 });
  await expect(page.getByTestId("intake-v6-header")).toBeVisible({ timeout: 60_000 });
}

export async function assertThreeStepProgressVisible(page: Page): Promise<void> {
  await expect(page.getByTestId("intake-v6-progress")).toBeVisible();
  await expect(page.getByTestId("intake-v6-progress-step-layers")).toBeVisible();
  await expect(page.getByTestId("intake-v6-progress-step-review")).toBeVisible();
  await expect(page.getByTestId("intake-v6-progress-step-confirm")).toBeVisible();

  for (const label of INTAKE_V6_VISIBLE_STEP_LABELS) {
    await expect(page.getByTestId("intake-v6-progress").getByText(label, { exact: true })).toBeVisible();
  }
}

export async function assertNoRemovedWorkspaceStatusBadge(page: Page): Promise<void> {
  await expect(page.getByTestId("intake-v6-workspace-status-badge")).toHaveCount(0);
  await expect(page.getByText("SVG ready")).toHaveCount(0);
}

export async function clickProgressStep(page: Page, step: "layers" | "review" | "confirm"): Promise<void> {
  await page.getByTestId(`intake-v6-progress-step-${step}`).click();
}

export async function assertHeaderStepLabel(page: Page, label: string): Promise<void> {
  await expect(page.getByTestId("intake-v6-header-step")).toHaveText(label);
}

export async function assertNoFalseCantWidthWarning(page: Page): Promise<void> {
  await expect(page.getByText("Verifică lățimea cantului.")).toHaveCount(0);
}

export async function assertNoFalseLegacyConfirmationCopy(page: Page): Promise<void> {
  await expect(page.getByText("RETURN_CANT_COMPONENT_CONFIRMATION_MISSING")).toHaveCount(0);
  await expect(page.getByText("Artwork neconfirmat în Review.")).toHaveCount(0);
}

/** @deprecated use assertNoFalseCantWidthWarning + assertNoFalseLegacyConfirmationCopy */
export async function assertFalseCantAndArtworkFlagWarnings(page: Page): Promise<void> {
  await assertNoFalseCantWidthWarning(page);
  await assertNoFalseLegacyConfirmationCopy(page);
}

export async function expandFinalConfigurationSummary(page: Page): Promise<void> {
  const summary = page.getByTestId("intake-v6-final-configuration-summary");
  await expect(summary).toBeVisible();
  const expanded = await summary.getAttribute("data-expanded");
  if (expanded !== "true") {
    await page.getByTestId("intake-v6-final-configuration-summary-toggle").click();
  }
  await expect(summary).toHaveAttribute("data-expanded", "true");
  await expect(page.getByTestId("intake-v6-confirm-dashboard")).toBeVisible();
}

export async function continueFromLayersIfReady(page: Page): Promise<void> {
  const continueBtn = page.getByTestId("intake-v6-footer-next");
  await expect(continueBtn).toBeVisible();
  if (await continueBtn.isEnabled()) {
    await continueBtn.click();
    await assertHeaderStepLabel(page, "Configurare");
  }
}

export async function continueFromReviewIfReady(page: Page): Promise<void> {
  const continueBtn = page.getByTestId("intake-v6-footer-next");
  await expect(continueBtn).toBeVisible();
  if (await continueBtn.isEnabled()) {
    await continueBtn.click();
    await assertHeaderStepLabel(page, "Confirmare");
  } else {
    await clickProgressStep(page, "confirm");
    await assertHeaderStepLabel(page, "Confirmare");
  }
}
