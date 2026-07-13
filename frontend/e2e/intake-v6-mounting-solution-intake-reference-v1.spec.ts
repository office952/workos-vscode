/**
 * Runtime evidence for PRODUCT_SYSTEM_MOUNTING_SOLUTION_INTAKE_REFERENCE_V1.
 */
import { expect, test, type Page, type Response } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const WORKSPACE_ID = "b00a3a0c-5a3d-4d0b-a95e-582bb542dde1";
const OPERATOR_URL = "http://127.0.0.1:3000/intake-v6/IR-MRI01769/operator";
const METAL_TEMPLATE = "TPL-METAL-PREMOUNT-STRUCTURE_v1";
const OUT_DIR = path.resolve(
  fileURLToPath(new URL(".", import.meta.url)),
  "../../docs/qa/product-system-mounting-solution-intake-reference-v1/screenshots",
);
const REPORT_PATH = path.resolve(
  fileURLToPath(new URL(".", import.meta.url)),
  "../../docs/qa/product-system-mounting-solution-intake-reference-v1/evidence_report.json",
);

type MountingSolutionPayload = {
  template_code?: string;
  configuration?: {
    bar_material?: string;
    mounting_bar_profile?: string;
    bar_count?: number;
  };
};

type FinishSetupPayload = {
  mounting_scope?: string;
  mounting_solution?: MountingSolutionPayload | null;
};

type ScenarioNote = {
  name: string;
  screenshot: string;
  mounting_scope: string;
  mounting_solution: string;
  selector_enabled: boolean;
  template_identity_visible: boolean;
  bar_material?: string;
  mounting_bar_profile?: string;
  bar_count?: string;
  selector_disabled?: boolean;
};

const notes: ScenarioNote[] = [];
const finishPutEvents: Array<{
  status: number;
  request_mounting_solution: MountingSolutionPayload | null | undefined;
  response_mounting_solution: MountingSolutionPayload | null | undefined;
}> = [];
const consoleErrors: string[] = [];
const networkErrors: string[] = [];

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

async function waitFinishPut(
  page: Page,
  predicate?: (body: FinishSetupPayload) => boolean,
): Promise<Response> {
  return page.waitForResponse(
    async (response) => {
      if (!response.url().includes("/finish-setup") || response.request().method() !== "PUT") {
        return false;
      }
      if (response.status() !== 200) {
        return false;
      }
      if (!predicate) {
        return true;
      }
      try {
        const body = response.request().postDataJSON() as FinishSetupPayload;
        return predicate(body);
      } catch {
        return false;
      }
    },
    { timeout: 120_000 },
  );
}

async function setMountingScope(page: Page, value: string) {
  const putPromise = waitFinishPut(page, (body) => body.mounting_scope === value);
  await page.getByTestId("intake-v6-mounting-scope").selectOption(value);
  await expect(page.getByTestId("intake-v6-mounting-scope")).toHaveValue(value, { timeout: 30_000 });
  const response = await putPromise;
  await recordFinishPut(response);
  await expect(page.getByTestId("intake-v6-review-autosave-status")).not.toContainText("așteaptă", {
    timeout: 120_000,
  });
  await page.waitForTimeout(1500);
}

async function recordFinishPut(response: Response) {
  const status = response.status();
  let requestBody: FinishSetupPayload | null = null;
  let responseBody: { payload?: { finish_setup?: FinishSetupPayload } } | null = null;
  try {
    requestBody = response.request().postDataJSON() as FinishSetupPayload;
  } catch {
    requestBody = null;
  }
  try {
    responseBody = (await response.json()) as { payload?: { finish_setup?: FinishSetupPayload } };
  } catch {
    responseBody = null;
  }
  finishPutEvents.push({
    status,
    request_mounting_solution: requestBody?.mounting_solution,
    response_mounting_solution: responseBody?.payload?.finish_setup?.mounting_solution,
  });
}

async function captureScenario(page: Page, name: string, screenshot: string) {
  const scope = await page.getByTestId("intake-v6-mounting-scope").inputValue();
  const solution = await page.getByTestId("intake-v6-mounting-solution-selector").inputValue();
  const selector = page.getByTestId("intake-v6-mounting-solution-selector");
  const selectorEnabled = await selector.isEnabled();
  const templateIdentityVisible =
    (await page.getByTestId("intake-v6-mounting-solution-template-identity").count()) > 0;
  const note: ScenarioNote = {
    name,
    screenshot,
    mounting_scope: scope,
    mounting_solution: solution,
    selector_enabled: selectorEnabled,
    template_identity_visible: templateIdentityVisible,
    selector_disabled: !selectorEnabled,
  };
  if (await page.getByTestId("intake-v6-mounting-solution-bar-material").count()) {
    note.bar_material = await page.getByTestId("intake-v6-mounting-solution-bar-material").inputValue();
    note.mounting_bar_profile = await page.getByTestId("intake-v6-mounting-solution-bar-profile").inputValue();
    note.bar_count = await page.getByTestId("intake-v6-mounting-solution-bar-count").inputValue();
  }
  await page.screenshot({ path: path.join(OUT_DIR, screenshot), fullPage: true });
  notes.push(note);
}

test.describe("Intake V6 mounting solution reference", () => {
  test.beforeAll(() => {
    fs.mkdirSync(OUT_DIR, { recursive: true });
  });

  test.use({ viewport: { width: 1440, height: 960 } });

  test("captures metal premount solution save/reload flow", async ({ page }) => {
    test.setTimeout(600_000);

    page.on("console", (msg) => {
      if (msg.type() === "error") {
        consoleErrors.push(msg.text());
      }
    });
    page.on("response", (response) => {
      if (response.status() >= 400) {
        networkErrors.push(`${response.status()} ${response.request().method()} ${response.url()}`);
      }
    });

    await gotoMontajTab(page);

    await setMountingScope(page, "preparation_only");

    const templatePut = waitFinishPut(
      page,
      (body) => body.mounting_solution?.template_code === METAL_TEMPLATE,
    );
    await page.getByTestId("intake-v6-mounting-solution-selector").selectOption(METAL_TEMPLATE);
    await expect(page.getByTestId("intake-v6-mounting-solution-template-identity")).toContainText(
      METAL_TEMPLATE,
      { timeout: 30_000 },
    );

    const configPut = waitFinishPut(page, (body) => {
      const config = body.mounting_solution?.configuration;
      return (
        body.mounting_solution?.template_code === METAL_TEMPLATE &&
        config?.bar_material === "aluminum" &&
        config?.mounting_bar_profile === "30x30x1.5" &&
        Number(config?.bar_count) === 3
      );
    });
    await page.getByTestId("intake-v6-mounting-solution-bar-material").selectOption("aluminum");
    await page.getByTestId("intake-v6-mounting-solution-bar-profile").selectOption("30x30x1.5");
    await page.getByTestId("intake-v6-mounting-solution-bar-count").fill("3");

    const templateResponse = await templatePut;
    await recordFinishPut(templateResponse);
    const configResponse = await configPut;
    await recordFinishPut(configResponse);

    const configResponseBody = (await configResponse.json()) as {
      payload?: { finish_setup?: FinishSetupPayload };
    };
    const persisted = configResponseBody.payload?.finish_setup?.mounting_solution;
    expect(persisted?.template_code).toBe(METAL_TEMPLATE);
    expect(persisted?.configuration).toMatchObject({
      bar_material: "aluminum",
      mounting_bar_profile: "30x30x1.5",
      bar_count: 3,
    });

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
      bar_material: "aluminum",
      mounting_bar_profile: "30x30x1.5",
      bar_count: "3",
    });

    await page.reload({ waitUntil: "networkidle" });
    await gotoMontajTab(page);
    await expect(page.getByTestId("intake-v6-mounting-solution-selector")).toHaveValue(METAL_TEMPLATE, {
      timeout: 60_000,
    });
    await expect(page.getByTestId("intake-v6-mounting-solution-bar-material")).toHaveValue("aluminum");
    await expect(page.getByTestId("intake-v6-mounting-solution-bar-profile")).toHaveValue("30x30x1.5");
    await expect(page.getByTestId("intake-v6-mounting-solution-bar-count")).toHaveValue("3");
    await captureScenario(page, "reload_preserved", "03_reload_preserved.png");

    await setMountingScope(page, "none");
    await expect(page.getByTestId("intake-v6-mounting-solution-selector")).toBeDisabled();
    await expect(page.getByTestId("intake-v6-mounting-solution-selector")).toHaveValue(METAL_TEMPLATE);
    await captureScenario(page, "scope_none_child_inactive", "04_scope_none_child_inactive.png");
  });

  test.afterAll(async () => {
    let schemaFreshness: Record<string, unknown> = { mounting_solution: "unknown" };
    try {
      const openapi = await fetch("http://127.0.0.1:8000/openapi.json");
      const body = (await openapi.json()) as {
        components?: { schemas?: { IntakeV4FinishSetup?: { properties?: Record<string, unknown> } } };
      };
      schemaFreshness = {
        openapi_ok: openapi.ok,
        mounting_solution: Boolean(body.components?.schemas?.IntakeV4FinishSetup?.properties?.mounting_solution),
      };
    } catch (error) {
      schemaFreshness = { openapi_ok: false, error: String(error) };
    }

    const savePutEvents = finishPutEvents.filter((event) => event.status === 200);
    const lastSavePut = savePutEvents.at(-1) ?? null;

    fs.writeFileSync(
      REPORT_PATH,
      JSON.stringify(
        {
          task: "PRODUCT_SYSTEM_MOUNTING_SOLUTION_INTAKE_REFERENCE_V1",
          closeout_task: "PRODUCT_SYSTEM_MOUNTING_SOLUTION_RUNTIME_QA_CLOSEOUT_V1",
          workspace_id: WORKSPACE_ID,
          route: OPERATOR_URL,
          captured_at: new Date().toISOString(),
          head: "f6dbb84",
          backend_startup_command:
            "powershell -NoProfile -ExecutionPolicy Bypass -File scripts/dev-backend.ps1",
          schema_freshness: schemaFreshness,
          finish_put_events: finishPutEvents,
          finish_put_count: finishPutEvents.length,
          finish_put_200_count: savePutEvents.length,
          last_put_status: lastSavePut?.status ?? null,
          last_response_mounting_solution: lastSavePut?.response_mounting_solution ?? null,
          reload_preserved:
            notes.find((note) => note.name === "reload_preserved")?.mounting_solution === METAL_TEMPLATE,
          scope_none_child_inactive:
            notes.find((note) => note.name === "scope_none_child_inactive")?.selector_disabled === true,
          historical_selection_preserved:
            notes.find((note) => note.name === "scope_none_child_inactive")?.mounting_solution === METAL_TEMPLATE,
          console_errors: consoleErrors,
          network_errors: networkErrors,
          scenarios: notes,
        },
        null,
        2,
      ),
    );
  });
});
