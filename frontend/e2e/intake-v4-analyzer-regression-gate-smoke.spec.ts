/**
 * One-off UI smoke for analyzer regression gate — run manually with stack up.
 * PW_SKIP_WEB_SERVER=1 npx playwright test e2e/intake-v4-analyzer-regression-gate-smoke.spec.ts
 */
import { expect, test } from "@playwright/test";
import path from "node:path";
import { fileURLToPath } from "node:url";

import {
  createIntakeV4WorkspaceForE2e,
  probeIntakeV4LiveBackend,
} from "./helpers/intakeV4Live";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const FIXTURE_DIR = path.resolve(__dirname, "../src/lib/svgAnalyzer/fixtures");

const FIXTURES = [
  {
    file: "pbl-layere.svg",
    productionPartCount: "10",
    layerRows: 3,
    widthMmContains: "2700.0 mm",
    heightMmContains: "350.0 mm",
    faceAreaContains: "0.69",
  },
  {
    file: "ana-maria-gradinita.svg",
    productionPartCount: null,
    layerRows: 6,
    widthMmContains: null,
    heightMmContains: null,
    faceAreaContains: null,
  },
  {
    file: "ana-maria-gradinita-fara-layere.svg",
    productionPartCount: null,
    layerRows: 6,
    widthMmContains: null,
    heightMmContains: null,
    faceAreaContains: null,
  },
] as const;

test.describe("analyzer regression gate UI smoke", () => {
  test.beforeAll(async () => {
    const probe = await probeIntakeV4LiveBackend();
    test.skip(!probe.backendHealthy, probe.reason ?? "backend down");
  });

  for (const fixture of FIXTURES) {
    test(`loads ${fixture.file}`, async ({ page }) => {
      const workspaceId = await createIntakeV4WorkspaceForE2e(`smoke-${fixture.file}`);
      await page.goto(`/intake-v4-app/${workspaceId}/operator`);
      await expect(page.getByText("Se verifică sesiunea")).toHaveCount(0, { timeout: 45_000 });
      await page.waitForSelector('[data-testid="intake-v4-operator-workspace"]', { timeout: 60_000 });

      const fileInput = page.getByTestId("intake-v4-svg-input");
      await fileInput.setInputFiles(path.join(FIXTURE_DIR, fixture.file));
      await expect(page.getByTestId("intake-v4-current-file")).toContainText(fixture.file, {
        timeout: 90_000,
      });
      await expect(page.getByTestId("intake-v4-analysis-summary")).toBeVisible({ timeout: 120_000 });
      await expect(page.getByTestId("intake-v4-layer-table")).toBeVisible({ timeout: 30_000 });

      const layerRows = page.locator('[data-testid="intake-v4-layer-table"] tbody tr');
      await expect(layerRows).toHaveCount(fixture.layerRows, { timeout: 30_000 });

      const confirmAll = page.getByTestId("intake-v4-confirm-all-roles");
      if (await confirmAll.isVisible()) {
        await confirmAll.click();
      }

      if (fixture.widthMmContains) {
        await expect(page.getByTestId("intake-v4-analysis-summary")).toContainText(
          fixture.widthMmContains,
          { timeout: 30_000 },
        );
      }

      if (fixture.heightMmContains) {
        await expect(page.getByTestId("intake-v4-analysis-summary")).toContainText(
          fixture.heightMmContains,
          { timeout: 30_000 },
        );
      }

      if (fixture.productionPartCount) {
        await expect(page.getByTestId("intake-v4-geometry-production-parts")).toContainText(
          fixture.productionPartCount,
          { timeout: 30_000 },
        );
      }

      if (fixture.faceAreaContains) {
        await expect(page.getByTestId("intake-v4-geometry-face-area")).toContainText(
          fixture.faceAreaContains,
          { timeout: 30_000 },
        );
      }
    });
  }
});
