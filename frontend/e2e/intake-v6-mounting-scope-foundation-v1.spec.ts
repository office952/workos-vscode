/**
 * Runtime evidence for INTAKE_V6_MOUNTING_SCOPE_FOUNDATION_V1.
 */
import { expect, test, type Page } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const OPERATOR_URL = "http://127.0.0.1:3000/intake-v6/IR-MRI01769/operator";
const OUT_DIR = path.resolve(
  fileURLToPath(new URL(".", import.meta.url)),
  "../../docs/qa/intake-v6-mounting-scope-foundation-v1/screenshots",
);
const REPORT_PATH = path.resolve(
  fileURLToPath(new URL(".", import.meta.url)),
  "../../docs/qa/intake-v6-mounting-scope-foundation-v1/evidence_report.json",
);

type ScenarioNote = {
  name: string;
  screenshot: string;
  mounting_scope: string;
  prep_section_active: boolean;
  site_section_active: boolean;
  prep_readonly: boolean;
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
  await expect(page.getByTestId("intake-v6-mounting-scope")).toBeVisible({ timeout: 60_000 });
  await page.waitForTimeout(1500);
}

async function setMountingScope(page: Page, value: string) {
  const put = page
    .waitForResponse(
      (r) => r.url().includes("/finish-setup") && r.request().method() === "PUT" && r.ok(),
      { timeout: 90_000 },
    )
    .catch(() => null);
  await page.getByTestId("intake-v6-mounting-scope").selectOption(value);
  await put;
  await expect(page.getByTestId("intake-v6-mounting-scope")).toHaveValue(value, { timeout: 30_000 });
  await page.waitForTimeout(3000);
}

async function captureScenario(page: Page, name: string, screenshot: string) {
  const scope = await page.getByTestId("intake-v6-mounting-scope").inputValue();
  const prepEnabled = await page.getByTestId("intake-v6-mounting-template-enabled").isEnabled();
  const siteVisible = (await page.getByTestId("intake-v6-site-installation-included").count()) > 0;
  await page.screenshot({ path: path.join(OUT_DIR, screenshot), fullPage: true });
  notes.push({
    name,
    screenshot,
    mounting_scope: scope,
    prep_section_active: prepEnabled,
    site_section_active: siteVisible,
    prep_readonly: !prepEnabled,
  });
}

test.describe("Intake V6 mounting scope foundation", () => {
  test.beforeAll(() => {
    fs.mkdirSync(OUT_DIR, { recursive: true });
  });

  test("captures mounting scope UI scenarios", async ({ page }) => {
    test.setTimeout(600_000);
    await gotoMontajTab(page);

    await setMountingScope(page, "none");
    await captureScenario(page, "mounting_none", "01_mounting_none.png");
    await expect(page.getByTestId("intake-v6-mounting-template-enabled")).toBeDisabled();
    await expect(page.getByTestId("intake-v6-mounting-prep-readonly-note")).toBeVisible();

    await setMountingScope(page, "preparation_only");
    await captureScenario(page, "preparation_only", "02_preparation_only.png");
    await expect(page.getByTestId("intake-v6-mounting-template-enabled")).toBeEnabled();
    await expect(page.getByTestId("intake-v6-mounting-site-inactive-note")).toBeVisible();

    await setMountingScope(page, "preparation_and_site_installation");
    await captureScenario(page, "preparation_and_site_installation", "03_preparation_and_site_installation.png");
    await expect(page.getByTestId("intake-v6-site-installation-included")).toBeVisible();

    await page.reload({ waitUntil: "domcontentloaded" });
    await gotoMontajTab(page);
    await captureScenario(page, "reload_preserved", "04_reload_preserved.png");
    await expect(page.getByTestId("intake-v6-mounting-scope")).toHaveValue("preparation_and_site_installation");
  });

  test.afterAll(() => {
    fs.writeFileSync(
      REPORT_PATH,
      JSON.stringify(
        {
          task: "INTAKE_V6_MOUNTING_SCOPE_FOUNDATION_V1",
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
