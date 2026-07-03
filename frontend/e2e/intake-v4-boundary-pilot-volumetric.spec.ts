/**
 * Intake V4 pilot volumetric — boundary E2E (analysis-bundle → Review → Confirm).
 *
 * Prerequisites:
 *   - scripts/start-dev.ps1 (backend :8000 + frontend :3000)
 *   - PW_SKIP_WEB_SERVER=1 when stack already running
 *   - npx playwright install chromium
 */

import { expect, test, type Page } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import {
  createIntakeV4WorkspaceForE2e,
  fetchIntakeV4MaterialBreakdown,
  fetchIntakeV4PricingPreview,
  fetchIntakeV4WorkspacePayload,
  probeIntakeV4LiveBackend,
} from "./helpers/intakeV4Live";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const FIXTURE_PBL = path.resolve(
  __dirname,
  "../src/lib/svgAnalyzer/fixtures/pbl-complex.svg",
);
const FIXTURE_REUPLOAD = path.join(__dirname, "fixtures/volumetric-letters-reupload.svg");

const FIXTURE_PBL_BASENAME = "pbl-complex.svg";
const FIXTURE_REUPLOAD_BASENAME = "volumetric-letters-reupload.svg";

let skipReason: string | undefined;

async function waitForAuthGate(page: Page) {
  await expect(page.getByText("Se verifică sesiunea")).toHaveCount(0, { timeout: 45_000 });
}

async function waitForV4WorkspaceReady(page: Page) {
  await page.waitForSelector('[data-testid="intake-v4-operator-workspace"]', { timeout: 60_000 });
  await expect(page.getByText("Loading workspace…")).toHaveCount(0, { timeout: 60_000 });
  const fileInput = page.getByTestId("intake-v4-svg-input");
  await fileInput.waitFor({ state: "attached", timeout: 30_000 });
  return fileInput;
}

async function importSvg(page: Page, fixturePath: string, basename: string) {
  const fileInput = await waitForV4WorkspaceReady(page);
  await fileInput.setInputFiles(fixturePath);
  await expect(page.getByTestId("intake-v4-current-file")).toContainText(basename, { timeout: 90_000 });
  await expect(page.getByTestId("intake-v4-analysis-summary")).toBeVisible({ timeout: 120_000 });
  await expect(page.getByTestId("intake-v4-layer-table")).toBeVisible({ timeout: 30_000 });
}

async function confirmAllLayerRoles(page: Page) {
  const confirmAll = page.getByTestId("intake-v4-confirm-all-roles");
  if (await confirmAll.isVisible().catch(() => false)) {
    await confirmAll.click();
  }
}

async function persistAnalysisBundleViaFooter(page: Page) {
  const nextBtn = page.getByTestId("intake-v4-footer-next");
  await expect(nextBtn).toBeEnabled({ timeout: 30_000 });
  await expect(nextBtn).toContainText("Setări");
  await nextBtn.click();
  await expect(page.getByTestId("intake-v4-step-review")).toBeVisible({ timeout: 90_000 });
  await expect(page.getByTestId("intake-v4-review-blocked")).toHaveCount(0);
}

function assertNoHardcodedBreakdownPrices(breakdown: Record<string, unknown>) {
  const rows = [
    ...((breakdown.material_rows as unknown[]) ?? []),
    ...((breakdown.consumable_rows as unknown[]) ?? []),
  ] as Array<Record<string, unknown>>;
  for (const row of rows) {
    expect(row.price_source).not.toBe("owner_fallback");
    if (row.unit_price != null) {
      expect(["pricing_registry", "owner_confirmed_fallback"]).toContain(row.price_source);
    }
  }
}

test.describe("Intake V4 boundary pilot volumetric", () => {
  test.beforeAll(async () => {
    if (!fs.existsSync(FIXTURE_PBL)) {
      skipReason = `Repo fixture missing: ${FIXTURE_PBL}`;
      return;
    }
    if (!fs.existsSync(FIXTURE_REUPLOAD)) {
      skipReason = `Reupload fixture missing: ${FIXTURE_REUPLOAD}`;
      return;
    }
    const probe = await probeIntakeV4LiveBackend();
    if (!probe.backendHealthy) {
      skipReason = probe.reason ?? "Intake V4 live backend unavailable";
    }
  });

  test.beforeEach(() => {
    test.skip(Boolean(skipReason), skipReason);
  });

  test("blocks Review before analysis-bundle persist (hash gate)", async ({ page }) => {
    test.setTimeout(180_000);

    const workspaceId = await createIntakeV4WorkspaceForE2e("e2e-v4-boundary-pre-persist");
    await page.goto(`/intake-v4-app/${workspaceId}/operator`);
    await waitForAuthGate(page);

    await importSvg(page, FIXTURE_PBL, FIXTURE_PBL_BASENAME);
    await confirmAllLayerRoles(page);

    const reviewStepBtn = page.getByTestId("intake-v4-progress-step-review");
    await expect(reviewStepBtn).toBeDisabled();
    await expect(page.getByTestId("intake-v4-step-review")).toHaveCount(0);

    await expect(page.getByTestId("intake-v4-smart-banner")).toContainText(/nesalvat|salveaz/i);
  });

  test("analysis-bundle → Review → Confirm with registry-safe breakdown", async ({ page }) => {
    test.setTimeout(300_000);

    const workspaceId = await createIntakeV4WorkspaceForE2e("e2e-v4-boundary-pilot");
    await page.goto(`/intake-v4-app/${workspaceId}/operator`);
    await waitForAuthGate(page);

    await importSvg(page, FIXTURE_PBL, FIXTURE_PBL_BASENAME);
    await confirmAllLayerRoles(page);
    await persistAnalysisBundleViaFooter(page);

    const payload = await fetchIntakeV4WorkspacePayload(workspaceId);
    expect(payload.svg_analysis_json).toBeTruthy();
    expect((payload.svg_source as Record<string, unknown>)?.file_hash).toBeTruthy();
    expect((payload.layer_role_setup as Record<string, unknown>)?.confirmation_status).toBe("complete");

    const nesting = (payload.svg_analysis_json as Record<string, unknown>)?.nesting as
      | Record<string, unknown>
      | undefined;
    if (nesting?.granularity != null) {
      expect(nesting.granularity).toBe("child-parts");
    }

    await expect(page.getByTestId("intake-v4-review-binding")).toBeVisible({ timeout: 30_000 });
    await expect(page.getByTestId("intake-v4-material-breakdown")).toBeVisible({ timeout: 45_000 });
    await expect(page.getByTestId("intake-v4-pricing-input-preview")).toBeVisible({ timeout: 45_000 });

    const breakdown = (await fetchIntakeV4MaterialBreakdown(workspaceId)) as Record<string, unknown>;
    assertNoHardcodedBreakdownPrices(breakdown);

    const pricing = (await fetchIntakeV4PricingPreview(workspaceId)) as Record<string, unknown>;
    const quoteInput = pricing.quote_input_payload as Record<string, unknown>;
    expect(quoteInput.intake_source).toBe("intake_v4");
    expect(
      quoteInput.letter_perimeter_m ?? quoteInput.total_letter_perimeter_ml ?? quoteInput.letter_count,
    ).toBeTruthy();

    const quoteGeom = payload.quote_geometry as Record<string, unknown> | undefined;
    if (quoteGeom?.letter_perimeter_m != null && quoteInput.letter_perimeter_m != null) {
      expect(Number(quoteInput.letter_perimeter_m)).toBe(Number(quoteGeom.letter_perimeter_m));
    }

    await page.getByTestId("intake-v4-confirm-finish").click();
    await expect(page.getByTestId("intake-v4-readiness")).toHaveAttribute(
      "data-readiness-status",
      "ready_for_quote_preview",
      { timeout: 30_000 },
    );

    const nextBtn = page.getByTestId("intake-v4-footer-next");
    await expect(nextBtn).toBeEnabled({ timeout: 15_000 });
    await nextBtn.click();

    await expect(page.getByTestId("intake-v4-step-confirm")).toBeVisible({ timeout: 30_000 });
    await expect(page.getByTestId("intake-v4-confirm-svg-file")).toContainText(FIXTURE_PBL_BASENAME);
    await expect(page.getByTestId("intake-v4-product-binding")).toBeVisible();
  });

  test("re-upload invalidates Review until analysis-bundle re-persisted", async ({ page }) => {
    test.setTimeout(300_000);

    const workspaceId = await createIntakeV4WorkspaceForE2e("e2e-v4-boundary-reupload");
    await page.goto(`/intake-v4-app/${workspaceId}/operator`);
    await waitForAuthGate(page);

    await importSvg(page, FIXTURE_PBL, FIXTURE_PBL_BASENAME);
    await confirmAllLayerRoles(page);
    await persistAnalysisBundleViaFooter(page);

    const perimeterBefore = await page.getByTestId("intake-v4-geometry-perimeter").innerText();

    await page.getByTestId("intake-v4-progress-step-layers").click();
    await importSvg(page, FIXTURE_REUPLOAD, FIXTURE_REUPLOAD_BASENAME);
    await confirmAllLayerRoles(page);

    await expect(page.getByTestId("intake-v4-progress-step-review")).toBeDisabled();
    await expect(page.getByTestId("intake-v4-step-review")).toHaveCount(0);

    await persistAnalysisBundleViaFooter(page);

    await expect(page.getByTestId("intake-v4-header-svg-file")).toContainText(FIXTURE_REUPLOAD_BASENAME, {
      timeout: 15_000,
    });
    const perimeterAfter = await page.getByTestId("intake-v4-geometry-perimeter").innerText();
    expect(perimeterAfter).not.toBe(perimeterBefore);

    const payload = await fetchIntakeV4WorkspacePayload(workspaceId);
    const svgSource = payload.svg_source as Record<string, unknown>;
    expect(String(svgSource.file_name)).toContain(FIXTURE_REUPLOAD_BASENAME);
  });
});
