/**
 * UI evidence for INTAKE_V6_SYSTEM_LED_COMMERCIAL_BUNDLE_UI_V1.
 * Scope changes are applied only through the operator UI (no direct API mutation).
 *
 * Run: cd frontend && $env:PW_SKIP_WEB_SERVER='1'; npx playwright test e2e/intake-v6-system-led-commercial-bundle-ui-v1.spec.ts
 */
import { expect, test, type Page } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const WORKSPACE_ROUTE_CODE = "IR-MRI01769";
const UI_BASE = process.env.INTAKE_V6_UI_BASE ?? "http://127.0.0.1:3000";
const OPERATOR_URL = `${UI_BASE}/intake-v6/${WORKSPACE_ROUTE_CODE}/operator`;

const OUT_DIR = path.resolve(
  fileURLToPath(new URL(".", import.meta.url)),
  "../../docs/qa/intake-v6-system-led-commercial-bundle-ui-v1/screenshots",
);
const REPORT_PATH = path.resolve(
  fileURLToPath(new URL(".", import.meta.url)),
  "../../docs/qa/intake-v6-system-led-commercial-bundle-ui-v1/evidence_report.json",
);

type PutRecord = {
  mode: string;
  sold_modules: string[];
  confirmed?: boolean;
};

type ScreenshotNote = {
  file: string;
  soldScope: string;
  systemLedBundleChecked: boolean;
  systemLedBundlePartial: boolean;
  advancedOpen: boolean;
  lightingChecked: boolean;
  electricalChecked: boolean;
  userClicks: string[];
  putCountDelta: number;
  submittedSoldModules: string[];
  materialTotal: string | null;
  materialRows: string[];
};

const notes: ScreenshotNote[] = [];

async function gotoOfferScopePanel(page: Page) {
  await page.getByTestId("intake-v6-progress-step-layers").click();
  await expect(page.getByTestId("intake-v6-offer-scope-panel")).toBeVisible({ timeout: 60_000 });
}

async function waitForOfferScopeConfirmed(page: Page) {
  const status = page.getByTestId("intake-v6-offer-scope-status");
  await expect(status).not.toContainText("Salvez selecția", { timeout: 120_000 });
  await expect(status).toHaveText("Selecție confirmată", { timeout: 30_000 });
}

async function clickWithPut(page: Page, testId: string) {
  const putPromise = page.waitForResponse(
    (response) =>
      response.url().includes("/offer-scope") &&
      response.request().method() === "PUT" &&
      response.ok(),
    { timeout: 120_000 },
  );
  await page.getByTestId(testId).click({ force: true });
  await putPromise;
  await waitForOfferScopeConfirmed(page);
}

async function expandAdvanced(page: Page) {
  const toggle = page.getByTestId("intake-v6-offer-scope-advanced-toggle");
  if ((await toggle.getAttribute("aria-expanded")) !== "true") {
    await toggle.click();
  }
  await expect(page.getByTestId("intake-v6-offer-scope-advanced-options")).toBeVisible();
}

async function readBundleState(page: Page) {
  const subsetVisible = await page.getByTestId("intake-v6-offer-scope-subset-options").isVisible();
  if (!subsetVisible) {
    return {
      systemLedBundleChecked: false,
      systemLedBundlePartial: false,
      advancedOpen: false,
      lightingChecked: false,
      electricalChecked: false,
    };
  }

  const bundle = page.getByTestId("intake-v6-offer-scope-system-led");
  const systemLedBundleChecked = await bundle.isChecked();
  const systemLedBundlePartial = await bundle.evaluate(
    (el) => (el as HTMLInputElement).indeterminate,
  );
  const advancedOpen = (await page.getByTestId("intake-v6-offer-scope-advanced-toggle").getAttribute("aria-expanded")) === "true";
  let lightingChecked = false;
  let electricalChecked = false;
  if (advancedOpen) {
    lightingChecked = await page.getByTestId("intake-v6-offer-scope-lighting").isChecked();
    electricalChecked = await page.getByTestId("intake-v6-offer-scope-electrical").isChecked();
  }
  return { systemLedBundleChecked, systemLedBundlePartial, advancedOpen, lightingChecked, electricalChecked };
}

async function readLiveCalcNotes(page: Page): Promise<{ materialTotal: string | null; materialRows: string[] }> {
  const total = page.getByTestId("intake-v6-live-material-total").first();
  const materialTotal = (await total.count()) > 0 ? ((await total.textContent()) ?? "").trim() : null;
  const rowLocator = page.locator('[data-testid^="intake-v6-live-material-used-"]');
  const count = await rowLocator.count();
  const materialRows: string[] = [];
  for (let i = 0; i < Math.min(count, 12); i += 1) {
    const text = ((await rowLocator.nth(i).textContent()) ?? "").replace(/\s+/g, " ").trim();
    if (text) materialRows.push(text);
  }
  return { materialTotal, materialRows };
}

async function captureScreenshot(
  page: Page,
  file: string,
  soldScope: string,
  meta: Omit<
    ScreenshotNote,
    | "file"
    | "soldScope"
    | "systemLedBundleChecked"
    | "systemLedBundlePartial"
    | "advancedOpen"
    | "lightingChecked"
    | "electricalChecked"
    | "materialTotal"
    | "materialRows"
  >,
) {
  const bundleState = await readBundleState(page);
  const { materialTotal, materialRows } = await readLiveCalcNotes(page);
  await page.screenshot({ path: path.join(OUT_DIR, file), fullPage: true });
  notes.push({
    file,
    soldScope,
    ...bundleState,
    materialTotal,
    materialRows,
    ...meta,
  });
}

test.describe("Intake V6 system LED commercial bundle UI evidence", () => {
  test.beforeAll(() => {
    fs.mkdirSync(OUT_DIR, { recursive: true });
    fs.mkdirSync(path.dirname(REPORT_PATH), { recursive: true });
  });

  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      sessionStorage.setItem("WORKOS_DEV_GUARD_BYPASS", "1");
    });
  });

  test("capture bundle UI states, transitions, and soak", async ({ page }) => {
    test.setTimeout(600_000);
    const putRecords: PutRecord[] = [];
    const putLog: Array<{ status: number; body: string }> = [];
    page.on("request", (request) => {
      if (request.method() === "PUT" && request.url().includes("/offer-scope")) {
        putRecords.push(JSON.parse(request.postData() ?? "{}") as PutRecord);
      }
    });
    page.on("response", async (response) => {
      if (response.url().includes("/offer-scope") && response.request().method() === "PUT") {
        putLog.push({
          status: response.status(),
          body: (await response.text()).slice(0, 500),
        });
      }
    });

    await page.goto(OPERATOR_URL, { waitUntil: "networkidle", timeout: 120_000 });
    await expect(page.getByTestId("intake-v6-header")).toBeVisible({ timeout: 120_000 });
    await gotoOfferScopePanel(page);

    if (!(await page.getByTestId("intake-v6-offer-scope-mode-full").isChecked())) {
      await clickWithPut(page, "intake-v6-offer-scope-mode-full");
    }

    const baselinePuts = putRecords.length;
    await page.getByTestId("intake-v6-offer-scope-mode-subset").click();
    await expect(page.getByTestId("intake-v6-offer-scope-subset-options")).toBeVisible();
    await captureScreenshot(page, "01_subset_bundle_ui_default.png", "subset-default", {
      userClicks: ["mode-subset"],
      putCountDelta: putRecords.length - baselinePuts,
      submittedSoldModules: putRecords.at(-1)?.sold_modules ?? [],
    });

    const beforeBundle = putRecords.length;
    await clickWithPut(page, "intake-v6-offer-scope-system-led");
    await captureScreenshot(page, "02_system_led_bundle_selected.png", "LIGHTING+ELECTRICAL", {
      userClicks: ["system-led"],
      putCountDelta: putRecords.length - beforeBundle,
      submittedSoldModules: putRecords.at(-1)?.sold_modules ?? [],
    });
    expect(putRecords.at(-1)?.sold_modules.sort()).toEqual(["ELECTRICAL", "LIGHTING"]);
    expect(putRecords.at(-1)?.sold_modules).not.toContain("SYSTEM_LED");

    await clickWithPut(page, "intake-v6-offer-scope-face");
    const beforeDeselect = putRecords.length;
    await clickWithPut(page, "intake-v6-offer-scope-system-led");
    await captureScreenshot(page, "03_system_led_bundle_deselected.png", "FACE-only", {
      userClicks: ["face", "system-led-deselect"],
      putCountDelta: putRecords.length - beforeDeselect,
      submittedSoldModules: putRecords.at(-1)?.sold_modules ?? [],
    });
    expect(putRecords.at(-1)?.sold_modules).toEqual(["FACE"]);

    await expandAdvanced(page);
    const beforeLighting = putRecords.length;
    await clickWithPut(page, "intake-v6-offer-scope-lighting");
    await captureScreenshot(page, "04_advanced_lighting_only.png", "FACE+LIGHTING", {
      userClicks: ["advanced-lighting"],
      putCountDelta: putRecords.length - beforeLighting,
      submittedSoldModules: putRecords.at(-1)?.sold_modules ?? [],
    });
    expect(await page.getByTestId("intake-v6-offer-scope-system-led").isChecked()).toBe(false);

    const beforeElectricalOnly = putRecords.length;
    await clickWithPut(page, "intake-v6-offer-scope-lighting");
    await clickWithPut(page, "intake-v6-offer-scope-electrical");
    await captureScreenshot(page, "05_advanced_electrical_only.png", "FACE+ELECTRICAL", {
      userClicks: ["advanced-electrical-only"],
      putCountDelta: putRecords.length - beforeElectricalOnly,
      submittedSoldModules: putRecords.at(-1)?.sold_modules ?? [],
    });

    const beforeBoth = putRecords.length;
    await clickWithPut(page, "intake-v6-offer-scope-lighting");
    await captureScreenshot(page, "06_advanced_both_reflects_bundle.png", "FACE+LIGHTING+ELECTRICAL", {
      userClicks: ["advanced-lighting", "advanced-electrical"],
      putCountDelta: putRecords.length - beforeBoth,
      submittedSoldModules: putRecords.at(-1)?.sold_modules ?? [],
    });
    expect(await page.getByTestId("intake-v6-offer-scope-system-led").isChecked()).toBe(true);

    const beforeFull = putRecords.length;
    await clickWithPut(page, "intake-v6-offer-scope-mode-full");
    await captureScreenshot(page, "07_full_product_regression.png", "full_product", {
      userClicks: ["mode-full"],
      putCountDelta: putRecords.length - beforeFull,
      submittedSoldModules: putRecords.at(-1)?.sold_modules ?? [],
    });
    expect(await page.getByTestId("intake-v6-offer-scope-mode-full").isChecked()).toBe(true);

    await page.reload({ waitUntil: "networkidle", timeout: 120_000 });
    await gotoOfferScopePanel(page);
    await expect(page.getByTestId("intake-v6-offer-scope-mode-full")).toBeChecked();
    await page.getByTestId("intake-v6-offer-scope-mode-subset").click();
    await clickWithPut(page, "intake-v6-offer-scope-system-led");
    await page.reload({ waitUntil: "networkidle", timeout: 120_000 });
    await gotoOfferScopePanel(page);
    await expandAdvanced(page);
    await captureScreenshot(page, "08_reload_hydrates_bundle_state.png", "LIGHTING+ELECTRICAL-reload", {
      userClicks: ["reload"],
      putCountDelta: 0,
      submittedSoldModules: ["LIGHTING", "ELECTRICAL"],
    });
    expect(await page.getByTestId("intake-v6-offer-scope-system-led").isChecked()).toBe(true);

    const transitionIds = [
      "intake-v6-offer-scope-back",
      "intake-v6-offer-scope-system-led",
      "intake-v6-offer-scope-system-led",
      "intake-v6-offer-scope-cant",
      "intake-v6-offer-scope-lighting",
      "intake-v6-offer-scope-electrical",
      "intake-v6-offer-scope-system-led",
      "intake-v6-offer-scope-face",
      "intake-v6-offer-scope-mode-full",
      "intake-v6-offer-scope-mode-subset",
    ] as const;

    const transitionStart = putRecords.length;
    for (const testId of transitionIds) {
      if (testId === "intake-v6-offer-scope-lighting" || testId === "intake-v6-offer-scope-electrical") {
        if (await page.getByTestId("intake-v6-offer-scope-subset-options").isVisible()) {
          await expandAdvanced(page);
        }
      }
      if (!(await page.getByTestId(testId).isVisible().catch(() => false))) {
        if (testId === "intake-v6-offer-scope-mode-subset") {
          await page.getByTestId("intake-v6-offer-scope-mode-subset").click({ force: true });
        }
        continue;
      }
      if (testId.includes("mode-subset")) {
        await page.getByTestId(testId).click({ force: true });
        continue;
      }
      await clickWithPut(page, testId);
      await expect(page.getByTestId("intake-v6-offer-scope-status")).not.toContainText("Salvez selecția", {
        timeout: 60_000,
      });
    }
    expect(putRecords.length - transitionStart).toBeGreaterThanOrEqual(1);

    await page.waitForTimeout(60_000);
    await expect(page.getByTestId("intake-v6-offer-scope-status")).not.toContainText("Salvez selecția", {
      timeout: 5_000,
    });

    fs.writeFileSync(
      REPORT_PATH,
      JSON.stringify(
        {
          task: "INTAKE_V6_SYSTEM_LED_COMMERCIAL_BUNDLE_UI_V1",
          workspace_code: WORKSPACE_ROUTE_CODE,
          route: OPERATOR_URL,
          captured_at: new Date().toISOString(),
          ui_driven: true,
          direct_api_used: false,
          system_led_persisted: false,
          put_records: putRecords,
          put_log: putLog,
          network_summary: {
            offer_scope_put_count: putLog.length,
            all_http_200: putLog.every((entry) => entry.status >= 200 && entry.status < 300),
          },
          sequential_transitions: transitionIds.length,
          soak_seconds: 60,
          screenshots: notes,
        },
        null,
        2,
      ),
    );

    expect(notes).toHaveLength(8);
    for (const record of putRecords) {
      expect(record.sold_modules).not.toContain("SYSTEM_LED");
    }
  });
});
