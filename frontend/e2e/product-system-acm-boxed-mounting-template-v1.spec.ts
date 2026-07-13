/**
 * Runtime evidence for PRODUCT_SYSTEM_ACM_BOXED_MOUNTING_TEMPLATE_V1.
 *
 * Flow A: standalone Product System template visibility (screenshots 01–04)
 * Flow B: Intake V6 linked child via mounting preparation selector (screenshots 05–07)
 */
import { expect, test, type Page, type Response } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ACM = "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1";
const METAL = "TPL-METAL-PREMOUNT-STRUCTURE_v1";
const WORKSPACE_ID = "b00a3a0c-5a3d-4d0b-a95e-582bb542dde1";
const OPERATOR_URL = "http://127.0.0.1:3000/intake-v6/IR-MRI01769/operator";
const PRODUCT_SYSTEM_URL = "http://127.0.0.1:3000/product-system";
const OUT_DIR = path.resolve(
  fileURLToPath(new URL(".", import.meta.url)),
  "../../docs/qa/product-system-acm-boxed-mounting-template-v1/screenshots",
);
const REPORT_PATH = path.resolve(
  fileURLToPath(new URL(".", import.meta.url)),
  "../../docs/qa/product-system-acm-boxed-mounting-template-v1/evidence_report.json",
);

type MountingSolutionPayload = {
  template_code?: string;
  configuration?: Record<string, unknown>;
};

type FinishSetupPayload = {
  mounting_scope?: string;
  mounting_solution?: MountingSolutionPayload | null;
};

type ScenarioNote = {
  name: string;
  screenshot: string;
  flow: "A" | "B";
  detail: string;
};

const scenarios: ScenarioNote[] = [];
const finishPutEvents: Array<{
  status: number;
  request_mounting_solution: MountingSolutionPayload | null | undefined;
  response_mounting_solution: MountingSolutionPayload | null | undefined;
}> = [];
const consoleErrors: string[] = [];
const networkErrors: string[] = [];

async function openProductSystem(page: Page) {
  await page.goto(PRODUCT_SYSTEM_URL, { waitUntil: "domcontentloaded", timeout: 120_000 });
  await expect(page.getByTestId("product-system-unified-catalog")).toBeVisible({ timeout: 60_000 });
  await page.waitForTimeout(2000);
}

async function expandLegacyBucket(page: Page) {
  const bucket = page.getByTestId("product-system-catalog-bucket-legacy-shared-modules");
  await expect(bucket).toBeVisible({ timeout: 60_000 });
  if ((await bucket.getAttribute("data-expanded")) !== "true") {
    await page.getByTestId("product-system-catalog-bucket-toggle-legacy-shared-modules").click();
    await expect(bucket).toBeVisible({ timeout: 10_000 });
    await page.waitForTimeout(800);
  }
}

async function gotoMontajTab(page: Page) {
  await page.goto(OPERATOR_URL, { waitUntil: "domcontentloaded", timeout: 120_000 });
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

async function captureScenario(
  page: Page,
  name: string,
  screenshot: string,
  flow: "A" | "B",
  detail: string,
) {
  await page.screenshot({ path: path.join(OUT_DIR, screenshot), fullPage: true });
  scenarios.push({ name, screenshot, flow, detail });
}

test.describe("Product System ACM boxed mounting template v1", () => {
  test.beforeAll(() => {
    fs.mkdirSync(OUT_DIR, { recursive: true });
  });

  test.use({ viewport: { width: 1440, height: 900 } });

  test("captures standalone catalog and linked-child mounting flows", async ({ page }) => {
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

    await openProductSystem(page);
    await captureScenario(
      page,
      "product_system_loaded",
      "01_product_system_catalog_loaded.png",
      "A",
      "Unified catalog shell",
    );

    await page.getByTestId("product-system-filter-candidate-products").click();
    await page.waitForTimeout(1200);
    await captureScenario(
      page,
      "candidate_filter",
      "02_candidate_products_filter.png",
      "A",
      "Candidate filter (may be empty)",
    );

    await page.getByTestId("product-system-filter-all").click();
    await expandLegacyBucket(page);
    await captureScenario(
      page,
      "legacy_bucket_expanded",
      "03_legacy_modules_bucket_acm_home.png",
      "A",
      "ACM listed as internal module",
    );

    const acmRow = page.getByTestId(`product-system-unified-row-${ACM}`);
    await expect(acmRow).toBeVisible({ timeout: 60_000 });
    await acmRow.click();
    await expect(page.getByTestId("product-system-template-detail-panel")).toBeVisible({ timeout: 30_000 });
    await captureScenario(page, "acm_detail_panel", "04_acm_template_detail_panel.png", "A", ACM);

    await gotoMontajTab(page);
    await setMountingScope(page, "preparation_only");
    await captureScenario(
      page,
      "montaj_preparation",
      "05_intake_montaj_preparation_scope.png",
      "B",
      "Mounting prep active",
    );

    const acmPut = waitFinishPut(page, (body) => body.mounting_solution?.template_code === ACM);
    await page.getByTestId("intake-v6-mounting-solution-selector").selectOption(ACM);
    await expect(page.getByTestId("intake-v6-mounting-acm-panel_width_mm")).toBeVisible({ timeout: 30_000 });
    const acmResponse = await acmPut;
    await recordFinishPut(acmResponse);
    await captureScenario(
      page,
      "acm_selected",
      "06_intake_acm_mounting_solution_selected.png",
      "B",
      "ACM linked child fields",
    );

    const metalPut = waitFinishPut(page, (body) => body.mounting_solution?.template_code === METAL);
    await page.getByTestId("intake-v6-mounting-solution-selector").selectOption(METAL);
    await expect(page.getByTestId("intake-v6-mounting-solution-bar-material")).toBeVisible({ timeout: 30_000 });
    const metalResponse = await metalPut;
    await recordFinishPut(metalResponse);
    await captureScenario(page, "metal_regression", "07_metal_premount_regression.png", "B", METAL);
  });

  test.afterAll(async () => {
    let schemaFreshness: Record<string, unknown> = {};
    try {
      const openapi = await fetch("http://127.0.0.1:8000/openapi.json");
      const body = await openapi.json();
      const text = JSON.stringify(body);
      schemaFreshness = {
        openapi_ok: openapi.ok,
        mounting_solution: text.includes("mounting_solution"),
        acm_template_reference: /ACM-BOXED-MOUNTING/i.test(text),
      };
    } catch (error) {
      schemaFreshness = { openapi_ok: false, error: String(error) };
    }

    let head = "unknown";
    try {
      const { execSync } = await import("node:child_process");
      head = execSync("git rev-parse --short HEAD", { encoding: "utf8" }).trim();
    } catch {
      head = "unknown";
    }

    const savePutEvents = finishPutEvents.filter((event) => event.status === 200);
    const lastSavePut = savePutEvents.at(-1) ?? null;

    let existingReport: Record<string, unknown> = {};
    if (fs.existsSync(REPORT_PATH)) {
      try {
        existingReport = JSON.parse(fs.readFileSync(REPORT_PATH, "utf8")) as Record<string, unknown>;
      } catch {
        existingReport = {};
      }
    }

    const officialPlaywrightSpec = {
      spec_path: "frontend/e2e/product-system-acm-boxed-mounting-template-v1.spec.ts",
      captured_at: new Date().toISOString(),
      head,
      workspace_id: WORKSPACE_ID,
      operator_route: OPERATOR_URL,
      product_system_route: PRODUCT_SYSTEM_URL,
      template_code: ACM,
      viewport: { width: 1440, height: 900 },
      wait_until: { product_system: "domcontentloaded", intake: "domcontentloaded" },
      schema_freshness: schemaFreshness,
      finish_put_events: finishPutEvents,
      finish_put_count: finishPutEvents.length,
      finish_put_200_count: savePutEvents.length,
      last_put_status: lastSavePut?.status ?? null,
      last_response_mounting_solution: lastSavePut?.response_mounting_solution ?? null,
      console_errors: consoleErrors,
      network_errors: networkErrors,
      scenarios,
      verdict: scenarios.length === 7 ? "PASS" : "PARTIAL",
    };

    fs.writeFileSync(
      REPORT_PATH,
      JSON.stringify(
        {
          ...existingReport,
          official_playwright_spec: officialPlaywrightSpec,
        },
        null,
        2,
      ),
    );
  });
});
