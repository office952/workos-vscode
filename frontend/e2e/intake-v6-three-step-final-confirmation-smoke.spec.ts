import { expect, test } from "@playwright/test";
import { mkdirSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  INTAKE_V6_THREE_STEP_SMOKE_WORKSPACE_ID,
  assertHeaderStepLabel,
  assertNoFalseCantWidthWarning,
  assertNoFalseLegacyConfirmationCopy,
  assertNoRemovedWorkspaceStatusBadge,
  assertThreeStepProgressVisible,
  clickProgressStep,
  continueFromLayersIfReady,
  continueFromReviewIfReady,
  expandFinalConfigurationSummary,
  gotoIntakeV6Operator,
} from "./helpers/intakeV6ThreeStepSmoke";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const EVIDENCE_DIR = path.resolve(
  __dirname,
  "../../../docs/qa/intake-v6-three-step-final-confirmation-e2e-smoke-alignment-v1",
);
mkdirSync(EVIDENCE_DIR, { recursive: true });

test.describe("Intake V6 three-step final confirmation smoke", () => {
  test("operator flow: Straturi → Configurare → Confirmare with single final confirmation", async ({
    page,
  }) => {
    // Step A — load workspace
    await gotoIntakeV6Operator(page, INTAKE_V6_THREE_STEP_SMOKE_WORKSPACE_ID);
    await assertThreeStepProgressVisible(page);
    await assertNoRemovedWorkspaceStatusBadge(page);
    await expect(page.getByTestId("intake-v6-header-workspace-code")).toBeVisible();

    // Step B — Pas 1 Straturi
    await clickProgressStep(page, "layers");
    await expect(page.getByTestId("intake-v6-layers-layout")).toBeVisible({ timeout: 30_000 });
    await expect(page.getByTestId("intake-v6-layers-operator-panel")).toBeVisible();
    await expect(page.getByTestId("intake-v6-layer-card-grid")).toBeVisible();
    await assertHeaderStepLabel(page, "Straturi");
    await continueFromLayersIfReady(page);

    // Step C — Pas 2 Configurare
    await expect(page.getByTestId("intake-v6-step-review")).toBeVisible({ timeout: 30_000 });
    await assertHeaderStepLabel(page, "Configurare");
    await expect(page.getByText(/Alb · 60 mm/).first()).toBeVisible();
    await expect(page.getByText("Print + laminare").first()).toBeVisible();
    await assertNoFalseCantWidthWarning(page);
    await assertNoFalseLegacyConfirmationCopy(page);
    await expect(page.getByTestId("intake-v6-confirm-internal-draft")).toHaveCount(0);

    // Real unresolved blocker remains (artwork classification), not a false cant warning
    const footerIssues = page.getByTestId("intake-v6-footer-issues");
    if (await footerIssues.isVisible()) {
      await expect(page.getByTestId("intake-v6-footer-issues-toggle")).toHaveAttribute("aria-expanded", "false");
    }

    // Step D — Pas 3 Confirmare (separate step)
    await continueFromReviewIfReady(page);
    await expect(page.getByTestId("intake-v6-step-confirm")).toBeVisible({ timeout: 30_000 });
    await expect(page.getByTestId("intake-v6-step-review")).toHaveCount(0);
    await assertHeaderStepLabel(page, "Confirmare");

    const summary = page.getByTestId("intake-v6-final-configuration-summary");
    await expect(summary).toBeVisible();
    await expect(summary).toHaveAttribute("data-expanded", "false");

    await expandFinalConfigurationSummary(page);
    await expect(page.getByRole("heading", { level: 2, name: "Confirmare finală" })).toBeVisible();

    const technicalDetails = page.getByTestId("intake-v6-final-configuration-technical-details");
    await expect(technicalDetails).toBeVisible();
    await expect(technicalDetails).toHaveAttribute("data-expanded", "false");

    await expect(page.getByTestId("intake-v6-confirm-internal-draft")).toBeVisible();
    await expect(page.getByTestId("intake-v6-create-internal-draft")).toBeVisible();
    await expect(page.getByTestId("intake-v6-create-internal-draft")).toBeDisabled();

    await page.screenshot({
      path: path.join(EVIDENCE_DIR, "three-step-smoke-pass.png"),
      fullPage: true,
    });
  });

  test("blocked scenario: final action stays guarded until final confirmation", async ({ page }) => {
    await gotoIntakeV6Operator(page, INTAKE_V6_THREE_STEP_SMOKE_WORKSPACE_ID);
    await clickProgressStep(page, "confirm");
    await expect(page.getByTestId("intake-v6-step-confirm")).toBeVisible({ timeout: 30_000 });

    await expandFinalConfigurationSummary(page);
    const finalCheckbox = page.getByTestId("intake-v6-confirm-internal-draft");
    await expect(finalCheckbox).toBeVisible();
    await expect(finalCheckbox).not.toBeChecked();

    const createDraft = page.getByTestId("intake-v6-create-internal-draft");
    await expect(createDraft).toBeDisabled();

    const primaryReason = page.getByTestId("intake-v6-footer-primary-action-reason");
    if (await primaryReason.isVisible()) {
      await expect(primaryReason).not.toHaveText(/Verifică lățimea cantului/i);
    }

    await assertNoFalseCantWidthWarning(page);
    await assertNoFalseLegacyConfirmationCopy(page);
  });

  test("final confirmation control exists only on Pas 3 (no quote mutation)", async ({ page }) => {
    await gotoIntakeV6Operator(page, INTAKE_V6_THREE_STEP_SMOKE_WORKSPACE_ID);
    await clickProgressStep(page, "review");
    await expect(page.getByTestId("intake-v6-confirm-internal-draft")).toHaveCount(0);

    await clickProgressStep(page, "confirm");
    await expandFinalConfigurationSummary(page);

    const finalCheckbox = page.getByTestId("intake-v6-confirm-internal-draft");
    await expect(finalCheckbox).toHaveCount(1);
    await expect(finalCheckbox).toBeEnabled();
    await expect(finalCheckbox).not.toBeChecked();

    const createDraft = page.getByTestId("intake-v6-create-internal-draft");
    await expect(createDraft).toBeVisible();
    await expect(createDraft).toBeDisabled();
    await expect(page.getByTestId("intake-v6-footer-primary-action-reason")).toBeVisible();
  });
});
