/**
 * UI smoke: Ana Maria unlayered SVG vs CorelDRAW reference curve lengths.
 *
 * Volumetric letter perimeter vs Corel (26.747 m) is validated in Vitest:
 * `ana-maria-corel-perimeter-diagnostic.test.ts` (layer-sum metric).
 * UI shows LED exterior perimeter (~20.88 m), not Corel total curve length.
 *
 * PW_SKIP_WEB_SERVER=1 when stack already on :3000 + :8000
 */
import { expect, test } from "@playwright/test";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { COREL_ANA_MARIA_REFERENCE } from "../src/lib/svgAnalyzer/analyzer/corelAnaMariaReference";
import {
  createIntakeV4WorkspaceForE2e,
  probeIntakeV4LiveBackend,
} from "./helpers/intakeV4Live";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const FIXTURE_DIR = path.resolve(__dirname, "../src/lib/svgAnalyzer/fixtures");
const FIXTURE = "ana-maria-gradinita-fara-layere.svg";
const FIXTURE_PATH = path.join(FIXTURE_DIR, FIXTURE);

test.describe("Ana Maria Corel reference perimeter UI smoke", () => {
  test.beforeAll(async () => {
    const probe = await probeIntakeV4LiveBackend();
    test.skip(!probe.backendHealthy, probe.reason ?? "backend down");
  });

  test("loads SVG, confirms six roles, and shows geometry quote metrics", async ({ page }) => {
    const workspaceId = await createIntakeV4WorkspaceForE2e("corel-perimeter-ana-maria");
    await page.goto(`/intake-v4-app/${workspaceId}/operator`);
    await expect(page.getByText("Se verifică sesiunea")).toHaveCount(0, { timeout: 45_000 });
    await page.waitForSelector('[data-testid="intake-v4-operator-workspace"]', { timeout: 60_000 });

    const fileInput = page.getByTestId("intake-v4-svg-input");
    await fileInput.setInputFiles(FIXTURE_PATH);
    await expect(page.getByTestId("intake-v4-current-file")).toContainText(FIXTURE, { timeout: 90_000 });
    await expect(page.getByTestId("intake-v4-analysis-summary")).toBeVisible({ timeout: 120_000 });

    const layerRows = page.locator('[data-testid="intake-v4-layer-table"] tbody tr');
    await expect(layerRows).toHaveCount(6, { timeout: 30_000 });

    const pseudoRows = page.locator('[data-testid="intake-v4-layer-table"] tbody tr', {
      hasText: /pseudo (gradinita|ana|maria|soare)/i,
    });
    await expect(pseudoRows).toHaveCount(4);

    const artworkRows = page.locator('[data-testid="intake-v4-layer-table"] tbody tr', {
      hasText: /logo (stanga|dreapta)/i,
    });
    await expect(artworkRows).toHaveCount(2);

    const confirmAll = page.getByTestId("intake-v4-confirm-all-roles");
    await expect(confirmAll).toBeVisible();
    await confirmAll.click();

    await expect(page.getByTestId("intake-v4-geometry-panel")).toBeVisible({ timeout: 30_000 });
    await expect(page.getByTestId("intake-v4-geometry-led-perimeter")).not.toHaveText("—");
    await expect(page.getByTestId("intake-v4-geometry-face-area")).not.toHaveText("—");

    const ledText = await page.getByTestId("intake-v4-geometry-led-perimeter").innerText();
    const ledM = Number.parseFloat(ledText.replace(/[^\d.]/g, ""));
    expect(ledM).toBeGreaterThan(0);

    // UI LED = exterior perimeter; Corel owner reference = total curve on letter fills.
    expect(ledM).toBeLessThan(COREL_ANA_MARIA_REFERENCE.volumetricLettersPerimeterM * 0.9);
    expect(ledM).toBeGreaterThan(COREL_ANA_MARIA_REFERENCE.volumetricLettersPerimeterM * 0.7);
  });
});
