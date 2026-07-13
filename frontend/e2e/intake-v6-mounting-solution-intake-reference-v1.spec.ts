/**
 * Runtime evidence for PRODUCT_SYSTEM_MOUNTING_SOLUTION_INTAKE_REFERENCE_V1.
 */
import { expect, test, type Page } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const OPERATOR_URL = "http://127.0.0.1:3000/intake-v6/IR-MRI01769/operator";
const OUT_DIR = path.resolve(
  fileURLToPath(new URL(".", import.meta.url)),
  "../../docs/qa/product-system-mounting-solution-intake-reference-v1/screenshots",
);
const REPORT_PATH = path.resolve(
  fileURLToPath(new URL(".", import.meta.url)),
  "../../docs/qa/product-system-mounting-solution-intake-reference-v1/evidence_report.json",
);

type ScenarioNote = {
  name: string;
  screenshot: string;
  mounting_scope: string;
  mounting_solution: string;
  selector_enabled: boolean;
  template_identity_visible: boolean;
};

const notes: ScenarioNote[] = [];

async function gotoMontajTab(page: Page) {
  await page.goto(OPERATOR_URL, { waitUntil: "networkidle", timeout: 120_000 });
  await expect(page.getByTestId("intake-v6-header")).toBeVisible({ timeout: 120_000 });
  const reviewStep = page.getByTestId("intake-v6-progress-step-review");
  await expect(reviewStep).toBeEnabled({ timeout: 60_000 });
  await reviewStep.click();
  await expect(page.getByTestId("intake-v6-step-review")).toBeVisible({ timeout: 60_000 });
  await page.getByTestId("intake-v6-review-tab-montaj").click();
  await expect(page.getByTestId("intake-v6-review-tab-panel-montaj")).toBeVisible({ timeout: 60_000 });
  await page.waitForTimeout(1500);
}

async function setMountingScope(page: Page, value: string) {
  await page.getByTestId("intake-v6-mounting-scope").selectOption(value);
  await expect(page.getByTestId("intake-v6-mounting-scope")).toHaveValue(value, { timeout: 30_000 });
  await page.waitForTimeout(2500);
}

async function captureScenario(page: Page, name: string, screenshot: string) {
  const scope = await page.getByTestId("intake-v6-mounting-scope").inputValue();
  const solution = await page.getByTestId("intake-v6-mounting-solution-selector").inputValue();
  const selectorEnabled = await page.getByTestId("intake-v6-mounting-solution-selector").isEnabled();
  const templateIdentityVisible =
    (await page.getByTestId("intake-v6-mounting-solution-template-identity").count()) > 0;
  await page.screenshot({ path: path.join(OUT_DIR, screenshot), fullPage: true });
  notes.push({
    name,
    screenshot,
    mounting_scope: scope,
    mounting_solution: solution,
    selector_enabled: selectorEnabled,
    template_identity_visible: templateIdentityVisible,
  });
}

test.describe("Intake V6 mounting solution reference", () => {
  test.beforeAll(() => {
    fs.mkdirSync(OUT_DIR, { recursive: true });
  });

  test.use({ viewport: { width: 1440, height: 960 } });

  test("captures metal premount solution save/reload flow", async ({ page }) => {
    test.setTimeout(600_000);
    await gotoMontajTab(page);

    await setMountingScope(page, "preparation_only");
    await page.getByTestId("intake-v6-mounting-solution-selector").selectOption("TPL-METAL-PREMOUNT-STRUCTURE_v1");
    await expect(page.getByTestId("intake-v6-mounting-solution-template-identity")).toContainText(
      "TPL-METAL-PREMOUNT-STRUCTURE_v1",
      { timeout: 30_000 },
    );
    await expect(page.getByTestId("intake-v6-review-autosave-status")).not.toContainText("așteaptă", {
      timeout: 120_000,
    });
    await captureScenario(page, "metal_solution_selected", "01_metal_solution_selected.png");

    await expect(page.getByTestId("intake-v6-live-calculation-sticky-shell")).toBeVisible({
      timeout: 120_000,
    });
    await page.getByTestId("intake-v6-live-calculation-sticky-shell").scrollIntoViewIfNeeded();
    await page.waitForTimeout(1500);
    await page.screenshot({ path: path.join(OUT_DIR, "02_linked_child_preview.png"), fullPage: true });
    notes.push({
      name: "linked_child_preview",
      screenshot: "02_linked_child_preview.png",
      mounting_scope: await page.getByTestId("intake-v6-mounting-scope").inputValue(),
      mounting_solution: await page.getByTestId("intake-v6-mounting-solution-selector").inputValue(),
      selector_enabled: true,
      template_identity_visible: true,
    });

    await page.reload({ waitUntil: "networkidle" });
    await gotoMontajTab(page);
    await expect(page.getByTestId("intake-v6-mounting-solution-selector")).toHaveValue(
      "TPL-METAL-PREMOUNT-STRUCTURE_v1",
      { timeout: 60_000 },
    );
    await captureScenario(page, "reload_preserved", "03_reload_preserved.png");

    await setMountingScope(page, "none");
    await expect(page.getByTestId("intake-v6-mounting-solution-selector")).toBeDisabled();
    await expect(page.getByTestId("intake-v6-mounting-solution-selector")).toHaveValue(
      "TPL-METAL-PREMOUNT-STRUCTURE_v1",
    );
    await captureScenario(page, "scope_none_child_inactive", "04_scope_none_child_inactive.png");
  });

  test.afterAll(() => {
    fs.writeFileSync(
      REPORT_PATH,
      JSON.stringify(
        {
          task: "PRODUCT_SYSTEM_MOUNTING_SOLUTION_INTAKE_REFERENCE_V1",
          workspace_id: "b00a3a0c-5a3d-4d0b-a95e-582bb542dde1",
          route: OPERATOR_URL,
          captured_at: new Date().toISOString(),
          scenarios: notes,
        },
        null,
        2,
      ),
    );
  });
});
