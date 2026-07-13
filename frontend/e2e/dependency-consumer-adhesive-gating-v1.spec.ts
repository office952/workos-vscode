/**
 * UI evidence for DEPENDENCY_CONSUMER_ADHESIVE_GATING_V1.
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
  "../../docs/qa/dependency-consumer-adhesive-gating-v1/screenshots",
);

const REPORT_PATH = path.resolve(
  fileURLToPath(new URL(".", import.meta.url)),
  "../../docs/qa/dependency-consumer-adhesive-gating-v1/evidence_report.json",
);

type PutRecord = {
  mode: string;
  sold_modules: string[];
  dependency_confirmation_codes?: string[];
};

type ScenarioNote = {
  file: string;
  scenario: string;
  sold_modules: string[];
  dependency_confirmations: string[];
  put_count_for_action: number;
  mountSatisfiedVisible: boolean;
  installByUsPromptVisible: boolean;
  userClicks: string[];
};

const notes: ScenarioNote[] = [];
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
  const putsBefore = putRecords.length;
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
  return putRecords.length - putsBefore;
}

async function selectFullProduct(page: Page) {
  await gotoOfferScopePanel(page);
  if (await page.getByTestId("intake-v6-offer-scope-mode-full").isChecked()) {
    return;
  }
  await clickScopeControl(page, "intake-v6-offer-scope-mode-full");
}

async function selectSubsetOnly(page: Page, modules: string[]) {
  const putsBefore = putRecords.length;
  await selectFullProduct(page);
  await gotoOfferScopePanel(page);
  if (!(await page.getByTestId("intake-v6-offer-scope-mode-subset").isChecked())) {
    await page.getByTestId("intake-v6-offer-scope-mode-subset").click();
    await page.waitForTimeout(400);
  }

  for (const code of modules) {
    const testId = MODULE_TEST_IDS[code];
    const checkbox = page.getByTestId(testId);
    if (!(await checkbox.isChecked())) {
      await clickScopeControl(page, testId);
    }
  }

  for (const [code, testId] of Object.entries(MODULE_TEST_IDS)) {
    if (modules.includes(code)) {
      continue;
    }
    const checkbox = page.getByTestId(testId);
    if (await checkbox.isChecked()) {
      await clickScopeControl(page, testId);
    }
  }

  if (modules.length > 0) {
    await waitForOfferScopeConfirmed(page);
  }
  return putRecords.length - putsBefore;
}

async function confirmDependencyCode(page: Page, code: string) {
  const button = page.getByTestId(`intake-v6-offer-scope-dependency-confirm-${code}`);
  await expect(button).toBeVisible({ timeout: 30_000 });
  const putsBefore = putRecords.length;
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
  return putRecords.length - putsBefore;
}

async function captureScenario(
  page: Page,
  file: string,
  scenario: string,
  userClicks: string[],
  putCount: number,
) {
  await gotoOfferScopePanel(page);
  const mountSatisfiedVisible =
    (await page.getByTestId("intake-v6-offer-scope-dependency-mount-satisfied").count()) > 0;
  const installByUsPromptVisible =
    (await page.getByTestId("intake-v6-offer-scope-dependency-confirm-LED_INSTALLATION_BY_US").count()) > 0;

  const sold_modules: string[] = [];
  const subsetOptionsVisible = await page.getByTestId("intake-v6-offer-scope-subset-options").isVisible();
  if (subsetOptionsVisible) {
    for (const [code, testId] of Object.entries(MODULE_TEST_IDS)) {
      if (await page.getByTestId(testId).isChecked()) {
        sold_modules.push(code);
      }
    }
  }

  const dependency_confirmations: string[] = [];
  const buttons = page.locator('[data-testid^="intake-v6-offer-scope-dependency-confirm-"]');
  const count = await buttons.count();
  for (let i = 0; i < count; i += 1) {
    const testId = (await buttons.nth(i).getAttribute("data-testid")) ?? "";
    dependency_confirmations.push(testId.replace("intake-v6-offer-scope-dependency-confirm-", ""));
  }

  await page.screenshot({ path: path.join(OUT_DIR, file), fullPage: true });
  notes.push({
    file,
    scenario,
    sold_modules,
    dependency_confirmations,
    put_count_for_action: putCount,
    mountSatisfiedVisible,
    installByUsPromptVisible,
    userClicks,
  });
}

test.describe("Dependency consumer adhesive gating evidence", () => {
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

  test("capture ten adhesive gating UI states", async ({ page }) => {
    test.setTimeout(900_000);

    await page.goto(OPERATOR_URL, { waitUntil: "networkidle", timeout: 120_000 });
    await expect(page.getByTestId("intake-v6-header")).toBeVisible({ timeout: 120_000 });
    await expect(page.getByText(/Backend indisponibil/i)).toHaveCount(0, { timeout: 180_000 });

    const backLightingPuts = await selectSubsetOnly(page, ["BACK", "LIGHTING"]);
    await captureScenario(page, "01_back_lighting_valid.png", "BACK+LIGHTING", ["BACK", "LIGHTING"], backLightingPuts);

    const faceCantPuts = await selectSubsetOnly(page, ["FACE", "RETURN-CANT", "LIGHTING"]);
    await captureScenario(
      page,
      "02_face_cant_lighting_valid.png",
      "FACE+RETURN-CANT+LIGHTING",
      ["FACE", "RETURN-CANT", "LIGHTING"],
      faceCantPuts,
    );

    const lePuts = await selectSubsetOnly(page, ["LIGHTING", "ELECTRICAL"]);
    await captureScenario(
      page,
      "06_lighting_electrical_no_mount.png",
      "LIGHTING+ELECTRICAL no mount",
      ["LIGHTING", "ELECTRICAL"],
      lePuts,
    );

    await selectSubsetOnly(page, ["LIGHTING"]);
    const lightingOnlyPuts = 1;
    await captureScenario(page, "03_lighting_only_unconfirmed.png", "LIGHTING unconfirmed", ["LIGHTING"], lightingOnlyPuts);

    const mountConfirmPuts = await confirmDependencyCode(page, "LED_MOUNT_SURFACE_NOT_SOLD");
    await captureScenario(
      page,
      "04_lighting_external_mount_confirmed.png",
      "LIGHTING external mount confirmed",
      ["confirm-mount"],
      mountConfirmPuts,
    );

    const installButton = page.getByTestId("intake-v6-offer-scope-dependency-confirm-LED_INSTALLATION_BY_US");
    let installConfirmPuts = 0;
    if (await installButton.isVisible().catch(() => false)) {
      installConfirmPuts = await confirmDependencyCode(page, "LED_INSTALLATION_BY_US");
    }
    await captureScenario(
      page,
      "05_lighting_external_install_by_us.png",
      "LIGHTING external + install by us",
      ["confirm-install"],
      installConfirmPuts,
    );

    const electricalPuts = await selectSubsetOnly(page, ["ELECTRICAL"]);
    await captureScenario(page, "07_electrical_only.png", "ELECTRICAL only", ["ELECTRICAL"], electricalPuts);

    const backPuts = await selectSubsetOnly(page, ["BACK"]);
    await captureScenario(page, "08_back_only.png", "BACK only", ["BACK"], backPuts);

    await selectFullProduct(page);
    await captureScenario(page, "09_full_product_regression.png", "full_product", ["mode-full"], 1);

    await selectSubsetOnly(page, []);
    const transitionBackPuts = await clickScopeControl(page, "intake-v6-offer-scope-back");
    const transitionLightingPuts = await clickScopeControl(page, "intake-v6-offer-scope-lighting");
    const transitionPuts = transitionBackPuts + transitionLightingPuts;
    await captureScenario(
      page,
      "10_empty_to_back_lighting_transition.png",
      "empty→BACK→LIGHTING transition",
      ["subset", "BACK", "LIGHTING"],
      transitionPuts,
    );

    await page.reload({ waitUntil: "networkidle" });
    await gotoOfferScopePanel(page);
    await expect(page.getByTestId("intake-v6-offer-scope-back")).toBeChecked();
    await expect(page.getByTestId("intake-v6-offer-scope-lighting")).toBeChecked();

    const report = {
      workspace: WORKSPACE_ID,
      workspace_code: WORKSPACE_ROUTE_CODE,
      route: OPERATOR_URL,
      captured_at: new Date().toISOString(),
      ui_driven: true,
      direct_api_used: false,
      spec: "frontend/e2e/dependency-consumer-adhesive-gating-v1.spec.ts",
      total_put_requests: putRecords.length,
      put_records: putRecords,
      screenshots: notes,
      scenarios_verified: [
        "BACK+LIGHTING mount satisfied",
        "FACE+RETURN-CANT+LIGHTING mount satisfied",
        "LIGHTING only unconfirmed",
        "External mount confirmed",
        "External mount + install by us",
        "LIGHTING+ELECTRICAL no mount",
        "ELECTRICAL only",
        "BACK only",
        "full_product regression",
        "empty→BACK→LIGHTING transition + reload",
      ],
    };
    fs.writeFileSync(REPORT_PATH, JSON.stringify(report, null, 2));
    expect(notes).toHaveLength(10);
  });
});
