/**
 * Visual evidence for INTAKE_V6_SOLD_SCOPE_FIELD_VISIBILITY_V1_1.
 * Run: cd frontend && npx playwright test e2e/intake-v6-sold-scope-field-visibility-v1.spec.ts
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
  "../../docs/qa/intake-v6-sold-scope-field-visibility-v1_1/screenshots",
);

async function selectSoldScope(
  page: import("@playwright/test").Page,
  modules: Array<"face" | "cant" | "back">,
) {
  await page.getByTestId("intake-v6-progress-step-layers").click();
  await expect(page.getByTestId("intake-v6-offer-scope-panel")).toBeVisible({ timeout: 60_000 });
  await page.getByTestId("intake-v6-offer-scope-mode-subset").click();
  for (const module of ["face", "cant", "back"] as const) {
    const testId = `intake-v6-offer-scope-${module === "cant" ? "cant" : module}`;
    const checkbox = page.getByTestId(testId);
    const shouldCheck = modules.includes(module);
    if (shouldCheck) {
      await checkbox.check();
    } else {
      await checkbox.uncheck();
    }
  }
  await expect(page.getByText(/Selecție confirmată/i)).toBeVisible({ timeout: 15_000 });
}

test.describe("Intake V6 sold scope field visibility evidence", () => {
  test.beforeAll(() => {
    fs.mkdirSync(OUT_DIR, { recursive: true });
  });

  test("capture step1 stability and review visibility states", async ({ page }) => {
    const workspaceId = INTAKE_V6_THREE_STEP_SMOKE_WORKSPACE_ID;
    const base = process.env.INTAKE_V6_UI_BASE ?? "http://127.0.0.1:3001";
    await page.goto(`${base}/intake-v6/${workspaceId}/operator`, {
      waitUntil: "networkidle",
      timeout: 120_000,
    });
    await expect(page.getByTestId("intake-v6-header")).toBeVisible({ timeout: 60_000 });

    await page.getByTestId("intake-v6-progress-step-layers").click();
    await expect(page.getByTestId("intake-v6-offer-scope-panel")).toBeVisible({ timeout: 60_000 });
    await page.waitForTimeout(3000);
    await page.screenshot({
      path: path.join(OUT_DIR, "01_step1_full_product_stable.png"),
      fullPage: true,
    });

    const scopes: Array<{ modules: Array<"face" | "cant" | "back">; file: string }> = [
      { modules: ["face"], file: "02_review_face_only.png" },
      { modules: ["cant"], file: "03_review_return_cant_only.png" },
      { modules: ["back"], file: "04_review_back_only.png" },
      { modules: ["face", "cant"], file: "05_review_face_return_cant.png" },
    ];

    for (const scope of scopes) {
      await selectSoldScope(page, scope.modules);
      await page.getByTestId("intake-v6-progress-step-review").click();
      await expect(page.getByTestId("intake-v6-review-step")).toBeVisible({ timeout: 60_000 });
      await page.screenshot({ path: path.join(OUT_DIR, scope.file), fullPage: true });
    }

    await selectSoldScope(page, ["face", "back"]);
    await page.getByTestId("intake-v6-progress-step-layers").click();
    await page.getByTestId("intake-v6-offer-scope-back").uncheck();
    await expect(page.getByText(/Selecție confirmată/i)).toBeVisible({ timeout: 15_000 });
    await page.getByTestId("intake-v6-progress-step-review").click();
    await page.screenshot({
      path: path.join(OUT_DIR, "06_reenabled_module_awaiting_reconfirmation.png"),
      fullPage: true,
    });
  });
});
