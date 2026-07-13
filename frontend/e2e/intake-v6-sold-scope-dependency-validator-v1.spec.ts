/**
 * UI evidence for INTAKE_V6_SOLD_SCOPE_DEPENDENCY_VALIDATOR_V1.
 * Scope and dependency confirmations are applied only through the operator UI.
 *
 * Run: cd frontend && $env:PW_SKIP_WEB_SERVER='1'; npx playwright test e2e/intake-v6-sold-scope-dependency-validator-v1.spec.ts
 */
import { expect, test, type Page } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const WORKSPACE_ID = "b00a3a0c-5a3d-4d0b-a95e-582bb542dde1";
const WORKSPACE_ROUTE_CODE = "IR-MRI01769";
const UI_BASE = process.env.INTAKE_V6_UI_BASE ?? "http://127.0.0.1:3000";
const OPERATOR_URL = `${UI_BASE}/intake-v6/${WORKSPACE_ROUTE_CODE}/operator`;

const OUT_DIR = path.resolve(
  fileURLToPath(new URL(".", import.meta.url)),
  "../../docs/qa/intake-v6-sold-scope-dependency-validator-v1/screenshots",
);

const REPORT_PATH = path.resolve(
  fileURLToPath(new URL(".", import.meta.url)),
  "../../docs/qa/intake-v6-sold-scope-dependency-validator-v1/evidence_report.json",
);

type PutRecord = {
  mode: string;
  sold_modules: string[];
  dependency_confirmation_codes?: string[];
};

type ScreenshotNote = {
  file: string;
  soldScope: string;
  dependencyFeedbackVisible: boolean;
  mountHintVisible: boolean;
  electricalHintVisible: boolean;
  mountSatisfiedVisible: boolean;
  confirmButtons: string[];
  userClicks: string[];
};

const notes: ScreenshotNote[] = [];
const putRecords: PutRecord[] = [];

const MODULE_TEST_IDS: Record<string, string> = {
  FACE: "intake-v6-offer-scope-face",
  "RETURN-CANT": "intake-v6-offer-scope-cant",
  BACK: "intake-v6-offer-scope-back",
  LIGHTING: "intake-v6-offer-scope-lighting",
  ELECTRICAL: "intake-v6-offer-scope-electrical",
};

async function gotoOfferScopePanel(page: Page) {
  await page.getByTestId("intake-v6-progress-step-layers").click();
  await expect(page.getByTestId("intake-v6-offer-scope-panel")).toBeVisible({ timeout: 60_000 });
}

async function waitForOfferScopeConfirmed(page: Page) {
  await gotoOfferScopePanel(page);
  const status = page.getByTestId("intake-v6-offer-scope-status");
  await expect(status).toBeVisible({ timeout: 60_000 });
  await expect(status).not.toContainText("Salvez selecția", { timeout: 120_000 });
  await expect(status).toHaveText("Selecție confirmată", { timeout: 60_000 });
}

async function clickScopeControl(page: Page, testId: string) {
  if (!(await page.getByTestId("intake-v6-offer-scope-panel").isVisible())) {
    await gotoOfferScopePanel(page);
  }
  const putPromise = page
    .waitForResponse(
      (response) =>
        response.url().includes("/offer-scope") &&
        response.request().method() === "PUT" &&
        response.ok(),
      { timeout: 120_000 },
    )
    .catch(() => null);
  await page.getByTestId(testId).click({ force: true });
  await putPromise;
  await waitForOfferScopeConfirmed(page);
}

async function selectFullProduct(page: Page) {
  await gotoOfferScopePanel(page);
  if (await page.getByTestId("intake-v6-offer-scope-mode-full").isChecked()) {
    return;
  }
  await clickScopeControl(page, "intake-v6-offer-scope-mode-full");
}

async function selectSubsetOnly(page: Page, modules: string[]) {
  await selectFullProduct(page);
  await gotoOfferScopePanel(page);
  await page.getByTestId("intake-v6-offer-scope-mode-subset").click();
  await page.waitForTimeout(400);

  if (modules.length === 0) {
    return;
  }

  for (const code of modules) {
    const testId = MODULE_TEST_IDS[code];
    const checkbox = page.getByTestId(testId);
    if (!(await checkbox.isChecked())) {
      await clickScopeControl(page, testId);
    }
  }
  await waitForOfferScopeConfirmed(page);
}

async function confirmDependencyCode(page: Page, code: string) {
  const button = page.getByTestId(`intake-v6-offer-scope-dependency-confirm-${code}`);
  await expect(button).toBeVisible({ timeout: 30_000 });
  const putPromise = page.waitForResponse(
    (response) =>
      response.url().includes("/offer-scope") &&
      response.request().method() === "PUT" &&
      response.ok(),
    { timeout: 120_000 },
  );
  await button.click();
  await putPromise;
  await waitForOfferScopeConfirmed(page);
}

async function readDependencyUi(page: Page): Promise<Omit<ScreenshotNote, "file" | "soldScope" | "userClicks">> {
  const feedback = page.getByTestId("intake-v6-offer-scope-dependency-feedback");
  const dependencyFeedbackVisible = (await feedback.count()) > 0;
  const mountHintVisible =
    (await page.getByTestId("intake-v6-offer-scope-dependency-mount-hint").count()) > 0;
  const electricalHintVisible =
    (await page.getByTestId("intake-v6-offer-scope-dependency-electrical-hint").count()) > 0;
  const mountSatisfiedVisible =
    (await page.getByTestId("intake-v6-offer-scope-dependency-mount-satisfied").count()) > 0;

  const confirmButtons: string[] = [];
  if (dependencyFeedbackVisible) {
    const buttons = page.locator('[data-testid^="intake-v6-offer-scope-dependency-confirm-"]');
    const count = await buttons.count();
    for (let i = 0; i < count; i += 1) {
      const testId = (await buttons.nth(i).getAttribute("data-testid")) ?? "";
      confirmButtons.push(testId.replace("intake-v6-offer-scope-dependency-confirm-", ""));
    }
  }

  return {
    dependencyFeedbackVisible,
    mountHintVisible,
    electricalHintVisible,
    mountSatisfiedVisible,
    confirmButtons,
  };
}

async function captureScreenshot(
  page: Page,
  file: string,
  soldScope: string,
  userClicks: string[],
) {
  await gotoOfferScopePanel(page);
  const ui = await readDependencyUi(page);
  await page.screenshot({ path: path.join(OUT_DIR, file), fullPage: true });
  notes.push({ file, soldScope, userClicks, ...ui });
}

test.describe("Intake V6 sold scope dependency validator evidence", () => {
  test.beforeAll(() => {
    fs.mkdirSync(OUT_DIR, { recursive: true });
    fs.mkdirSync(path.dirname(REPORT_PATH), { recursive: true });
  });

  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      sessionStorage.setItem("WORKOS_DEV_GUARD_BYPASS", "1");
    });
    page.on("request", (request) => {
      if (request.method() === "PUT" && request.url().includes("/offer-scope")) {
        putRecords.push(JSON.parse(request.postData() ?? "{}") as PutRecord);
      }
    });
  });

  test("capture ten dependency validator UI states", async ({ page }) => {
    test.setTimeout(480_000);

    await page.goto(OPERATOR_URL, {
      waitUntil: "networkidle",
      timeout: 120_000,
    });
    await expect(page.getByTestId("intake-v6-header")).toBeVisible({ timeout: 120_000 });
    await expect(page.getByText(/Backend indisponibil/i)).toHaveCount(0, { timeout: 180_000 });
    await gotoOfferScopePanel(page);
    await selectFullProduct(page);
    await captureScreenshot(page, "01_full_product_no_dependency_feedback.png", "full_product", [
      "mode-full",
    ]);

    await selectSubsetOnly(page, ["LIGHTING"]);
    await captureScreenshot(page, "02_lighting_only_mount_confirmation_required.png", "LIGHTING", [
      "mode-subset",
      "LIGHTING",
    ]);

    await confirmDependencyCode(page, "LED_MOUNT_SURFACE_NOT_SOLD");
    await captureScreenshot(page, "03_lighting_mount_confirmed.png", "LIGHTING + mount confirmed", [
      "confirm-LED_MOUNT_SURFACE_NOT_SOLD",
    ]);

    await selectSubsetOnly(page, ["BACK", "LIGHTING"]);
    await captureScreenshot(page, "04_back_lighting_mount_satisfied.png", "BACK+LIGHTING", [
      "BACK",
      "LIGHTING",
    ]);

    await selectSubsetOnly(page, ["FACE", "RETURN-CANT", "LIGHTING"]);
    await captureScreenshot(page, "05_face_cant_lighting_mount_satisfied.png", "FACE+RETURN-CANT+LIGHTING", [
      "FACE",
      "RETURN-CANT",
      "LIGHTING",
    ]);

    await selectSubsetOnly(page, ["ELECTRICAL"]);
    await captureScreenshot(page, "06_electrical_only_load_confirmation_required.png", "ELECTRICAL", [
      "ELECTRICAL",
    ]);

    await confirmDependencyCode(page, "ELECTRICAL_LOAD_NOT_SOLD");
    await captureScreenshot(page, "07_electrical_load_confirmed.png", "ELECTRICAL + load confirmed", [
      "confirm-ELECTRICAL_LOAD_NOT_SOLD",
    ]);

    await selectSubsetOnly(page, ["LIGHTING", "ELECTRICAL"]);
    await captureScreenshot(page, "08_lighting_electrical_dual_confirmation_required.png", "LIGHTING+ELECTRICAL", [
      "LIGHTING",
      "ELECTRICAL",
    ]);

    await gotoOfferScopePanel(page);
    for (const testId of Object.values(MODULE_TEST_IDS)) {
      const checkbox = page.getByTestId(testId);
      if (await checkbox.isChecked()) {
        await checkbox.uncheck();
      }
    }
    await expect(page.getByTestId("intake-v6-offer-scope-empty-subset-error")).toBeVisible({
      timeout: 15_000,
    });
    await captureScreenshot(page, "09_empty_subset_blocked.png", "empty subset", ["uncheck-all"]);

    await gotoOfferScopePanel(page);
    await page.getByTestId("intake-v6-offer-scope-back").check({ force: true });
    await waitForOfferScopeConfirmed(page);
    await page.getByTestId("intake-v6-offer-scope-lighting").check({ force: true });
    await waitForOfferScopeConfirmed(page);
    await page.reload({ waitUntil: "networkidle", timeout: 120_000 });
    await gotoOfferScopePanel(page);
    await expect(page.getByTestId("intake-v6-offer-scope-back")).toBeChecked();
    await expect(page.getByTestId("intake-v6-offer-scope-lighting")).toBeChecked();
    await captureScreenshot(page, "10_reload_preserves_back_lighting_scope.png", "BACK+LIGHTING after reload", [
      "reload",
    ]);

    fs.writeFileSync(
      REPORT_PATH,
      JSON.stringify(
        {
          workspace: WORKSPACE_ID,
          workspace_code: "IR-MRI01769",
          route: OPERATOR_URL,
          captured_at: new Date().toISOString(),
          ui_driven: true,
          direct_api_used: false,
          put_records: putRecords,
          screenshots: notes,
        },
        null,
        2,
      ),
    );

    expect(notes[1]?.dependencyFeedbackVisible).toBe(true);
    expect(notes[1]?.confirmButtons).toContain("LED_MOUNT_SURFACE_NOT_SOLD");
    expect(notes[2]?.confirmButtons).not.toContain("LED_MOUNT_SURFACE_NOT_SOLD");
    expect(notes[3]?.mountSatisfiedVisible).toBe(true);
    expect(notes[4]?.mountSatisfiedVisible).toBe(true);
    expect(notes[5]?.confirmButtons).toContain("ELECTRICAL_LOAD_NOT_SOLD");
    expect(notes[7]?.confirmButtons).toContain("LED_MOUNT_SURFACE_NOT_SOLD");
    expect(notes[7]?.confirmButtons).not.toContain("ELECTRICAL_LOAD_NOT_SOLD");
    expect(notes[8]?.dependencyFeedbackVisible || notes[8]?.mountHintVisible).toBeTruthy();
  });
});
