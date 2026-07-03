/**
 * Intake V4 — full operator flow with a complex real-world SVG (optional).
 *
 * Prerequisites:
 *   - scripts/start-dev.ps1 (backend :8000 + frontend :3000)
 *   - PW_SKIP_WEB_SERVER=1 when stack already running
 *   - INTAKE_V4_E2E_SVG_PATH pointing at a local SVG (skipped when unset or missing)
 */

import { expect, test, type Page } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

import { createIntakeV4WorkspaceForE2e, probeIntakeV4LiveBackend } from "./helpers/intakeV4Live";

const COMPLEX_SVG = process.env.INTAKE_V4_E2E_SVG_PATH?.trim();
const FIXTURE_BASENAME = COMPLEX_SVG ? path.basename(COMPLEX_SVG) : "complex.svg";

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

async function importPblComplex(page: Page) {
  if (!COMPLEX_SVG) throw new Error("INTAKE_V4_E2E_SVG_PATH not set");
  const fileInput = await waitForV4WorkspaceReady(page);
  await fileInput.setInputFiles(COMPLEX_SVG);

  await expect(page.getByTestId("intake-v4-current-file")).toContainText(FIXTURE_BASENAME, {
    timeout: 30_000,
  });
  await expect(page.getByTestId("intake-v4-svg-preview")).toBeVisible({ timeout: 30_000 });
  await expect(page.getByTestId("intake-v4-analysis-summary")).toBeVisible({ timeout: 90_000 });
  await expect(page.getByTestId("intake-v4-layer-table")).toBeVisible({ timeout: 30_000 });
  await expect(page.getByTestId("intake-v4-error")).toHaveCount(0);
}

async function confirmLayersAndGoToReview(page: Page) {
  const confirmAll = page.getByTestId("intake-v4-confirm-all-roles");
  if (await confirmAll.isVisible().catch(() => false)) {
    await confirmAll.click();
  }

  const nextBtn = page.getByTestId("intake-v4-footer-next");
  await expect(nextBtn).toBeEnabled({ timeout: 30_000 });
  await expect(nextBtn).toContainText("Setări");
  await nextBtn.click();

  await expect(page.getByTestId("intake-v4-step-review")).toBeVisible({ timeout: 60_000 });
}

test.describe("Intake V4 complex SVG (optional env fixture)", () => {
  test.beforeAll(async () => {
    if (!COMPLEX_SVG) {
      skipReason = "INTAKE_V4_E2E_SVG_PATH not set";
      return;
    }
    if (!fs.existsSync(COMPLEX_SVG)) {
      skipReason = `INTAKE_V4_E2E_SVG_PATH file missing: ${COMPLEX_SVG}`;
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

  test("import → review (materials + task preview) → confirm", async ({ page }) => {
    test.setTimeout(240_000);

    const workspaceId = await createIntakeV4WorkspaceForE2e("e2e-pbl-complex-desktop");
    await page.goto(`/intake-v4-app/${workspaceId}/operator`);
    await waitForAuthGate(page);

    await importPblComplex(page);
    await confirmLayersAndGoToReview(page);

    await expect(page.getByTestId("intake-v4-review-binding")).toBeVisible({ timeout: 30_000 });
    await expect(page.getByTestId("intake-v4-face-finish")).toBeVisible();
    await expect(page.getByTestId("intake-v4-lighting-fields")).toBeVisible();

    await expect(page.getByTestId("intake-v4-material-breakdown")).toBeVisible({ timeout: 30_000 });
    await expect(page.getByTestId("intake-v4-task-preview")).toBeVisible({ timeout: 30_000 });

    await page.getByTestId("intake-v4-confirm-finish").click();
    await expect(page.getByTestId("intake-v4-readiness")).toContainText("ready_for_quote_preview", {
      timeout: 30_000,
    });

    const nextBtn = page.getByTestId("intake-v4-footer-next");
    await expect(nextBtn).toBeEnabled({ timeout: 15_000 });
    await nextBtn.click();

    await expect(page.getByTestId("intake-v4-step-confirm")).toBeVisible({ timeout: 30_000 });
    await expect(page.getByTestId("intake-v4-confirm-svg-file")).toContainText(FIXTURE_BASENAME);
    await expect(page.getByTestId("intake-v4-product-binding")).toBeVisible();
  });

  test("drag-drop complex SVG loads preview", async ({ page }) => {
    test.setTimeout(240_000);

    if (!COMPLEX_SVG) throw new Error("INTAKE_V4_E2E_SVG_PATH not set");

    const workspaceId = await createIntakeV4WorkspaceForE2e("e2e-pbl-complex-drop");
    await page.goto(`/intake-v4-app/${workspaceId}/operator`);
    await waitForAuthGate(page);
    await waitForV4WorkspaceReady(page);

    const b64 = fs.readFileSync(COMPLEX_SVG).toString("base64");
    const dataTransfer = await page.evaluateHandle(
      ({ name, type, payloadB64 }) => {
        const bin = atob(payloadB64);
        const arr = new Uint8Array(bin.length);
        for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
        const dt = new DataTransfer();
        dt.items.add(new File([arr], name, { type }));
        return dt;
      },
      { name: FIXTURE_BASENAME, type: "image/svg+xml", payloadB64: b64 },
    );

    await page.getByTestId("intake-v4-operator-workspace-file-drop").dispatchEvent("drop", {
      dataTransfer,
    });

    await expect(page.getByTestId("intake-v4-current-file")).toContainText(FIXTURE_BASENAME, {
      timeout: 30_000,
    });
    await expect(page.getByTestId("intake-v4-svg-preview")).toBeVisible({ timeout: 30_000 });
    await expect(page.getByTestId("intake-v4-analysis-summary")).toBeVisible({ timeout: 90_000 });
    await expect(page.getByTestId("intake-v4-operator-workspace-file-drop-notice")).toContainText(
      FIXTURE_BASENAME,
      { timeout: 15_000 },
    );
  });
});
