/**
 * Runtime evidence for INTAKE_V6_STEP2_LED_MASTER_SOLD_SCOPE_GATE_V1.
 */
import { expect, test, type Page } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const OPERATOR_URL = "http://127.0.0.1:3000/intake-v6/IR-MRI01769/operator";
const OUT_DIR = path.resolve(
  fileURLToPath(new URL(".", import.meta.url)),
  "../../docs/qa/intake-v6-step2-led-master-sold-scope-gate-v1/screenshots",
);
const REPORT_PATH = path.resolve(
  fileURLToPath(new URL(".", import.meta.url)),
  "../../docs/qa/intake-v6-step2-led-master-sold-scope-gate-v1/evidence_report.json",
);

type ScenarioNote = {
  name: string;
  screenshot: string;
  sold_modules: string[];
  led_master_visible: boolean;
  led_master_editable: boolean;
  readonly_message: boolean;
  electrical_visible: boolean;
  lighting_visible: boolean;
};

const notes: ScenarioNote[] = [];

async function gotoOfferScope(page: Page) {
  await page.getByTestId("intake-v6-progress-step-layers").click();
  await expect(page.getByTestId("intake-v6-offer-scope-panel")).toBeVisible({ timeout: 60_000 });
}

async function waitScopeSaved(page: Page) {
  const status = page.getByTestId("intake-v6-offer-scope-status");
  await expect(status).not.toContainText("Salvez selecția", { timeout: 120_000 });
}

async function toggleScopeControl(page: Page, testId: string) {
  const put = page
    .waitForResponse(
      (r) => r.url().includes("/offer-scope") && r.request().method() === "PUT" && r.ok(),
      { timeout: 120_000 },
    )
    .catch(() => null);
  await page.getByTestId(testId).click({ force: true });
  await put;
  await waitScopeSaved(page);
}

async function setChecked(page: Page, testId: string, checked: boolean) {
  const box = page.getByTestId(testId);
  if ((await box.isChecked()) !== checked) {
    await toggleScopeControl(page, testId);
  }
}

async function setSoldModules(page: Page, modules: string[]) {
  await gotoOfferScope(page);
  await setChecked(page, "intake-v6-offer-scope-mode-subset", true);
  await expandAdvanced(page);

  const want = new Set(modules);
  const wantSystemLed =
    want.has("LIGHTING") && want.has("ELECTRICAL") && !want.has("FACE") && !want.has("RETURN-CANT") && !want.has("BACK");

  await setChecked(page, "intake-v6-offer-scope-system-led", false);
  await setChecked(page, "intake-v6-offer-scope-face", want.has("FACE"));
  await setChecked(page, "intake-v6-offer-scope-cant", want.has("RETURN-CANT"));
  await setChecked(page, "intake-v6-offer-scope-back", want.has("BACK"));
  await setChecked(page, "intake-v6-offer-scope-lighting", want.has("LIGHTING"));
  await setChecked(page, "intake-v6-offer-scope-electrical", want.has("ELECTRICAL"));

  if (wantSystemLed) {
    await setChecked(page, "intake-v6-offer-scope-system-led", true);
  }
}

async function selectFullProduct(page: Page) {
  await gotoOfferScope(page);
  await setChecked(page, "intake-v6-offer-scope-mode-full", true);
}

async function expandAdvanced(page: Page) {
  const toggle = page.getByTestId("intake-v6-offer-scope-advanced-toggle");
  await expect(toggle).toBeVisible({ timeout: 30_000 });
  if ((await toggle.getAttribute("aria-expanded")) !== "true") {
    await toggle.click();
  }
}

async function gotoIluminare(page: Page) {
  await page.getByTestId("intake-v6-progress-step-review").click();
  await expect(page.getByTestId("intake-v6-step-review")).toBeVisible({ timeout: 60_000 });
  await page.getByTestId("intake-v6-review-tab-iluminare").click();
  await expect(page.getByTestId("intake-v6-review-tab-panel-iluminare")).toBeVisible({ timeout: 30_000 });
}

async function readIluminareState(page: Page): Promise<Omit<ScenarioNote, "name" | "screenshot" | "sold_modules">> {
  const master = page.getByTestId("intake-v6-illuminated");
  const readonly = page.getByTestId("intake-v6-led-master-readonly");
  return {
    led_master_visible: (await master.count()) > 0,
    led_master_editable: (await master.count()) > 0,
    readonly_message: (await readonly.count()) > 0,
    electrical_visible: (await page.getByTestId("intake-v6-electrical-subsection").count()) > 0,
    lighting_visible: (await page.getByTestId("intake-v6-lighting-subsection").count()) > 0,
  };
}

test.describe("Step 2 LED master sold-scope gate", () => {
  test("capture four UI states", async ({ page }) => {
    test.setTimeout(600_000);
    fs.mkdirSync(OUT_DIR, { recursive: true });

    await page.goto(OPERATOR_URL, { waitUntil: "networkidle", timeout: 120_000 });
    await expect(page.getByTestId("intake-v6-header")).toBeVisible({ timeout: 120_000 });

    await setSoldModules(page, ["ELECTRICAL"]);
    await expandAdvanced(page);
    await expect(page.getByTestId("intake-v6-offer-scope-electrical")).toBeChecked();
    await expect(page.getByTestId("intake-v6-offer-scope-lighting")).not.toBeChecked();

    await gotoIluminare(page);
    await page.screenshot({ path: path.join(OUT_DIR, "01_electrical_only_no_led_master_input.png"), fullPage: true });
    notes.push({
      name: "ELECTRICAL-only",
      screenshot: "01_electrical_only_no_led_master_input.png",
      sold_modules: ["ELECTRICAL"],
      ...(await readIluminareState(page)),
    });
    expect(await page.getByTestId("intake-v6-illuminated").count()).toBe(0);
    expect(await page.getByTestId("intake-v6-led-master-readonly").count()).toBe(1);

    await setSoldModules(page, ["LIGHTING"]);

    await gotoIluminare(page);
    await page.screenshot({ path: path.join(OUT_DIR, "02_lighting_only_led_master_available.png"), fullPage: true });
    notes.push({
      name: "LIGHTING-only",
      screenshot: "02_lighting_only_led_master_available.png",
      sold_modules: ["LIGHTING"],
      ...(await readIluminareState(page)),
    });
    expect(await page.getByTestId("intake-v6-illuminated").count()).toBe(1);

    await setSoldModules(page, ["LIGHTING", "ELECTRICAL"]);

    await gotoIluminare(page);
    await page.screenshot({ path: path.join(OUT_DIR, "03_system_led_led_master_available.png"), fullPage: true });
    notes.push({
      name: "SYSTEM_LED",
      screenshot: "03_system_led_led_master_available.png",
      sold_modules: ["LIGHTING", "ELECTRICAL"],
      ...(await readIluminareState(page)),
    });
    expect(await page.getByTestId("intake-v6-illuminated").count()).toBe(1);

    await setSoldModules(page, ["LIGHTING", "ELECTRICAL"]);
    await gotoIluminare(page);
    expect(await page.getByTestId("intake-v6-illuminated").count()).toBe(1);

    await gotoOfferScope(page);
    await expandAdvanced(page);
    await setChecked(page, "intake-v6-offer-scope-lighting", false);
    await gotoIluminare(page);
    expect(await page.getByTestId("intake-v6-illuminated").count()).toBe(0);

    await setSoldModules(page, ["LIGHTING", "ELECTRICAL"]);
    await gotoIluminare(page);
    await page.screenshot({ path: path.join(OUT_DIR, "04_reenable_lighting_restores_state.png"), fullPage: true });
    notes.push({
      name: "Re-enable LIGHTING",
      screenshot: "04_reenable_lighting_restores_state.png",
      sold_modules: ["LIGHTING", "ELECTRICAL"],
      ...(await readIluminareState(page)),
    });
    expect(await page.getByTestId("intake-v6-illuminated").count()).toBe(1);

    fs.writeFileSync(
      REPORT_PATH,
      JSON.stringify({ task: "INTAKE_V6_STEP2_LED_MASTER_SOLD_SCOPE_GATE_V1", scenarios: notes }, null, 2),
    );
  });
});
