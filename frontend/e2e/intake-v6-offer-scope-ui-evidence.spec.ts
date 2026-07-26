/**
 * One-off visual evidence for INTAKE_V6_SOLD_MODULES_UI_V1.
 * Run: cd frontend && npx playwright test e2e/intake-v6-offer-scope-ui-evidence.spec.ts --config playwright.config.ts
 */
import { expect, test } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import {
  INTAKE_V6_THREE_STEP_SMOKE_WORKSPACE_ID,
  gotoIntakeV6Operator,
} from "./helpers/intakeV6ThreeStepSmoke";

const OUT_DIR = path.resolve(
  fileURLToPath(new URL(".", import.meta.url)),
  "../../docs/qa/intake-v6-sold-modules-ui-v1/screenshots",
);

test.describe("Intake V6 offer scope UI evidence", () => {
  test.beforeAll(() => {
    fs.mkdirSync(OUT_DIR, { recursive: true });
  });

  test("capture offer scope selector states", async ({ page }) => {
    const workspaceId = INTAKE_V6_THREE_STEP_SMOKE_WORKSPACE_ID;
    const base = process.env.INTAKE_V6_UI_BASE ?? "http://127.0.0.1:3001";
    await page.goto(`${base}/intake-v6/${workspaceId}/operator`, {
      waitUntil: "networkidle",
      timeout: 120_000,
    });
    await expect(page.getByTestId("intake-v6-header")).toBeVisible({ timeout: 60_000 });
    await page.getByTestId("intake-v6-progress-step-layers").click();
    await expect(page.getByTestId("intake-v6-svg-analyzer-step")).toBeVisible({ timeout: 60_000 });

    const panel = page.getByTestId("intake-v6-offer-scope-panel");
    await expect(panel).toBeVisible({ timeout: 60_000 });

    await page.screenshot({
      path: path.join(OUT_DIR, "01_step1_full_product_default.png"),
      fullPage: true,
    });

    await page.getByTestId("intake-v6-offer-scope-mode-subset").click();
    await page.getByTestId("intake-v6-offer-scope-face").check();
    await page.getByTestId("intake-v6-offer-scope-cant").check();
    await expect(panel.getByText(/Selecție confirmată|Salvez selecția/i)).toBeVisible({ timeout: 15_000 });

    await page.screenshot({
      path: path.join(OUT_DIR, "02_step1_subset_face_cant_selected.png"),
      fullPage: true,
    });

    await page.getByTestId("intake-v6-offer-scope-face").uncheck();
    await page.getByTestId("intake-v6-offer-scope-cant").uncheck();
    await expect(page.getByTestId("intake-v6-offer-scope-empty-subset-error")).toBeVisible();

    await page.screenshot({
      path: path.join(OUT_DIR, "03_step1_empty_subset_validation.png"),
      fullPage: true,
    });
  });
});
