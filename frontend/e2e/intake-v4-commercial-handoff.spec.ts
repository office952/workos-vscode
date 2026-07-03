/**
 * Intake V4 commercial handoff — Confirm → draft quote → QuoteWizard.
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
  assertIntakeV4CommercialLinkage,
  assertQuoteInputHasNoCommercialTotals,
  createIntakeV4DraftQuoteRaw,
  createIntakeV4WorkspaceForE2e,
  fetchEntityQuoteByCode,
  fetchIntakeV4PricingPreview,
  fetchIntakeV4WorkspacePayload,
  getPersistedAnalysisFileHash,
  intakeV4LinkageCode,
  parseIntakeV4LinkageFromQuoteNotes,
  probeIntakeV4LiveBackend,
  sha256HexFromFile,
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

async function resolveArtworkExecutionsIfPresent(page: Page) {
  const section = page.getByTestId("intake-v4-artwork-finishes");
  if (!(await section.isVisible().catch(() => false))) return;
  const selects = page.locator('[data-testid^="intake-v4-artwork-execution-"]');
  const count = await selects.count();
  for (let i = 0; i < count; i++) {
    await selects.nth(i).selectOption("print_laminate");
  }
}

async function completeReviewAndOpenConfirm(page: Page) {
  await resolveArtworkExecutionsIfPresent(page);
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
}

async function runV4PilotThroughConfirm(page: Page, workspaceId: string) {
  await page.goto(`/intake-v4-app/${workspaceId}/operator`);
  await waitForAuthGate(page);
  await importSvg(page, FIXTURE_PBL, FIXTURE_PBL_BASENAME);
  await confirmAllLayerRoles(page);
  await persistAnalysisBundleViaFooter(page);
  await completeReviewAndOpenConfirm(page);
}

async function acceptConfirmHandoffCheckboxes(page: Page) {
  await page.getByTestId("intake-v4-confirm-draft-only").check();
  await page.getByTestId("intake-v4-confirm-no-order").check();
  await page.getByTestId("intake-v4-confirm-no-execution").check();
  await page.getByTestId("intake-v4-confirm-no-inventory").check();
}

test.describe("Intake V4 commercial handoff", () => {
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

  test("Confirm → draft quote → QuoteWizard with IV4 snapshot linkage", async ({ page }) => {
    test.setTimeout(360_000);

    const workspaceId = await createIntakeV4WorkspaceForE2e("e2e-v4-commercial-handoff");
    await runV4PilotThroughConfirm(page, workspaceId);

    const pricingBefore = (await fetchIntakeV4PricingPreview(workspaceId)) as Record<string, unknown>;
    const quoteInputBefore = pricingBefore.quote_input_payload as Record<string, unknown>;
    assertQuoteInputHasNoCommercialTotals(quoteInputBefore);

    await acceptConfirmHandoffCheckboxes(page);

    const draftResponsePromise = page.waitForResponse(
      (res) =>
        res.url().includes(`/intake-v4/workspaces/${workspaceId}/create-draft-quote`) &&
        res.request().method() === "POST",
      { timeout: 60_000 },
    );

    await page.getByTestId("intake-v4-open-quote-wizard").click();

    const draftResponse = await draftResponsePromise;
    const draftBody = (await draftResponse.json()) as Record<string, unknown>;
    if (draftResponse.status() !== 201) {
      throw new Error(
        `create-draft-quote expected 201, got ${draftResponse.status()}: ${JSON.stringify(draftBody).slice(0, 500)}`,
      );
    }
    expect(draftBody.quote_created).toBe(true);
    expect(draftBody.requires_pricing_review).toBe(true);
    expect(draftBody.source_module).toBe("intake_v4");
    expect(draftBody.source_workspace_id).toBe(workspaceId);
    expect(draftBody.order_created).toBe(false);
    expect(draftBody.execution_plan_created).toBe(false);
    expect(draftBody.inventory_mutated).toBe(false);

    const quoteInput = draftBody.quote_input_payload as Record<string, unknown>;
    assertQuoteInputHasNoCommercialTotals(quoteInput);

    const quoteCode = String(draftBody.quote_code);
    await page.waitForURL(new RegExp(`/quotes/${quoteCode.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}`), {
      timeout: 45_000,
    });

    await expect(page.getByText("Cum vrei să calculezi?")).toBeVisible({ timeout: 45_000 });

    const entityQuote = await fetchEntityQuoteByCode(quoteCode);
    expect(entityQuote).toBeTruthy();
    expect(entityQuote!.status).toBe("draft");
    expect(entityQuote!.intake_code).toBe(intakeV4LinkageCode(workspaceId));
    expect(Number(entityQuote!.grand_total ?? -1)).toBe(0);

    const linkage = parseIntakeV4LinkageFromQuoteNotes(entityQuote!.notes);
    expect(linkage).toBeTruthy();
    assertIntakeV4CommercialLinkage(linkage!, workspaceId, quoteInput);

    const lineItems = JSON.parse(entityQuote!.line_items ?? "[]") as Array<Record<string, unknown>>;
    expect(lineItems.length).toBeGreaterThan(0);
    for (const row of lineItems) {
      expect(row.unit_price).toBe(0);
      expect(row.total).toBe(0);
      expect(row.price_source).toBeUndefined();
    }

    const payload = await fetchIntakeV4WorkspacePayload(workspaceId);
    const quoteGeom = payload.quote_geometry as Record<string, unknown> | undefined;
    if (quoteGeom?.letter_perimeter_m != null && quoteInput.letter_perimeter_m != null) {
      expect(Number(quoteInput.letter_perimeter_m)).toBe(Number(quoteGeom.letter_perimeter_m));
    }
  });

  test("Confirm handoff UI blocked after re-upload without analysis-bundle re-persist", async ({
    page,
  }) => {
    test.setTimeout(360_000);

    const workspaceId = await createIntakeV4WorkspaceForE2e("e2e-v4-handoff-stale-ui");
    await runV4PilotThroughConfirm(page, workspaceId);

    await page.getByTestId("intake-v4-progress-step-layers").click();
    await importSvg(page, FIXTURE_REUPLOAD, FIXTURE_REUPLOAD_BASENAME);
    await confirmAllLayerRoles(page);

    await expect(page.getByTestId("intake-v4-progress-step-review")).toBeDisabled();
    await expect(page.getByTestId("intake-v4-progress-step-confirm")).toBeDisabled();
    await expect(page.getByTestId("intake-v4-step-confirm")).toHaveCount(0);
    await expect(page.getByTestId("intake-v4-smart-banner")).toContainText(/nesalvat|salveaz/i);
  });

  test("create-draft-quote API blocked when client hash is stale after re-upload", async ({
    page,
  }) => {
    test.setTimeout(360_000);

    const workspaceId = await createIntakeV4WorkspaceForE2e("e2e-v4-handoff-stale-api");
    await runV4PilotThroughConfirm(page, workspaceId);

    await page.getByTestId("intake-v4-progress-step-layers").click();
    await importSvg(page, FIXTURE_REUPLOAD, FIXTURE_REUPLOAD_BASENAME);
    await confirmAllLayerRoles(page);

    const persistedHash = await getPersistedAnalysisFileHash(workspaceId);
    const localReuploadHash = sha256HexFromFile(FIXTURE_REUPLOAD);
    expect(localReuploadHash).not.toBe(persistedHash);

    const stale = await createIntakeV4DraftQuoteRaw(workspaceId, {
      client_analysis_hash: localReuploadHash,
    });
    expect(stale.status).toBe(422);
    const detail = stale.body.detail as Record<string, unknown> | undefined;
    expect(detail?.error).toBe("QUOTE_HANDOFF_BLOCKED");
    const blockers = (detail?.blockers as string[] | undefined) ?? [];
    expect(blockers).toContain("analysis_hash_mismatch");
  });
});
