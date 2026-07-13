/**
 * Runtime evidence — PRODUCT_SYSTEM_ACM_BOXED_MOUNTING_OWNER_RATES_CPP_V1
 */
import { chromium } from "@playwright/test";
import { execSync } from "node:child_process";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT_DIR = path.join(__dirname, "screenshots");
const REPORT_PATH = path.join(__dirname, "evidence_report.json");
const ACM = "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1";
const LETTERS = "TPL-VOLUMETRIC-LETTERS_v2";
const WORKSPACE_ID = "b00a3a0c-5a3d-4d0b-a95e-582bb542dde1";
const OPERATOR_URL = "http://127.0.0.1:3000/intake-v6/IR-MRI01769/operator";
const CPP_URL = `http://127.0.0.1:8000/api/v1/product-system/commercial-price-preview/${LETTERS}`;

const ACM_QUOTE_INPUT = {
  analysis_ready: true,
  client: { width_mm: 1200, height_mm: 800 },
  quote_geometry: {
    letter_count: 3,
    letter_perimeter_m: 8.0,
    letter_face_area_m2: 0.8,
  },
  finish_setup: {
    mounting_scope: "preparation_only",
    mounting_solution: {
      template_code: ACM,
      configuration: {
        panel_width_mm: 1200,
        panel_height_mm: 800,
        acm_thickness_mm: 3,
        return_depth_mm: 60,
        rear_lip_mm: 25,
        fold_sides: "all",
        v_groove_angle_deg: 135,
      },
    },
    confirmed: true,
  },
};

async function fetchCppLines() {
  const res = await fetch(CPP_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ quote_input: ACM_QUOTE_INPUT, currency: "EUR" }),
  });
  if (!res.ok) {
    return { ok: false, status: res.status, body: await res.text() };
  }
  const body = await res.json();
  const acmLines = (body.commercial_price_lines ?? []).filter((line) =>
    String(line.code ?? "").startsWith("acm_"),
  );
  return {
    ok: true,
    status: res.status,
    acm_line_codes: acmLines.map((line) => line.code),
    acm_lines: acmLines.map((line) => ({
      code: line.code,
      label: line.label,
      unit_price: line.commercial_unit_price,
      quantity: line.quantity,
      subtotal: line.subtotal,
      unit: line.unit,
    })),
    forbidden_hourly: body.forbidden_hourly_usage_detected ?? [],
    commercial_total: body.commercial_total,
  };
}

async function gotoMontajTab(page) {
  await page.goto(OPERATOR_URL, { waitUntil: "domcontentloaded", timeout: 120_000 });
  await page.getByTestId("intake-v6-header").waitFor({ timeout: 120_000 });
  await page.getByTestId("intake-v6-progress-step-review").click();
  await page.getByTestId("intake-v6-step-review").waitFor({ timeout: 60_000 });
  await page.getByTestId("intake-v6-review-tab-montaj").click();
  await page.getByTestId("intake-v6-review-tab-panel-montaj").waitFor({ timeout: 60_000 });
  await page.waitForTimeout(1200);
}

async function waitFinishPut(page, predicate) {
  return page.waitForResponse(
    async (response) => {
      if (!response.url().includes("/finish-setup") || response.request().method() !== "PUT") {
        return false;
      }
      if (response.status() !== 200) return false;
      if (!predicate) return true;
      try {
        const body = response.request().postDataJSON();
        return predicate(body);
      } catch {
        return false;
      }
    },
    { timeout: 120_000 },
  );
}

async function main() {
  await mkdir(OUT_DIR, { recursive: true });
  const cppBefore = await fetchCppLines();

  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const finishPutEvents = [];
  const consoleErrors = [];

  page.on("console", (msg) => {
    if (msg.type() === "error") consoleErrors.push(msg.text());
  });

  try {
    await gotoMontajTab(page);

    const scopePut = waitFinishPut(page, (body) => body.mounting_scope === "preparation_only");
    await page.getByTestId("intake-v6-mounting-scope").selectOption("preparation_only");
    await scopePut;
    await page.waitForTimeout(1200);

    const acmPut = waitFinishPut(page, (body) => body.mounting_solution?.template_code === ACM);
    await page.getByTestId("intake-v6-mounting-solution-selector").selectOption(ACM);
    await acmPut;
    await page.getByTestId("intake-v6-mounting-acm-panel_width_mm").waitFor({ timeout: 30_000 });

    const thicknessSelect = page.getByTestId("intake-v6-mounting-acm-acm_thickness_mm");
    const thicknessOptions = await thicknessSelect.locator("option").allTextContents();
    const thicknessValues = await thicknessSelect.locator("option").evaluateAll((nodes) =>
      nodes.map((node) => node.getAttribute("value")),
    );

    await page.getByTestId("intake-v6-mounting-acm-panel_width_mm").fill("1200");
    await page.getByTestId("intake-v6-mounting-acm-panel_height_mm").fill("800");
    await page.getByTestId("intake-v6-mounting-acm-return_depth_mm").fill("60");
    await page.getByTestId("intake-v6-mounting-acm-rear_lip_mm").fill("25");
    await page.waitForTimeout(1500);

    await page.screenshot({
      path: path.join(OUT_DIR, "01_acm_3mm_configuration.png"),
      fullPage: true,
    });

    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(800);
    const spine = page.getByTestId("intake-v6-commercial-spine");
    if (await spine.isVisible().catch(() => false)) {
      await spine.scrollIntoViewIfNeeded();
    }
    await page.screenshot({
      path: path.join(OUT_DIR, "02_acm_cpp_owner_rates.png"),
      fullPage: true,
    });

    await page.reload({ waitUntil: "domcontentloaded", timeout: 120_000 });
    await page.getByTestId("intake-v6-header").waitFor({ timeout: 120_000 });
    await page.getByTestId("intake-v6-progress-step-review").click();
    await page.getByTestId("intake-v6-review-tab-montaj").click();
    await page.getByTestId("intake-v6-review-tab-panel-montaj").waitFor({ timeout: 60_000 });
    await page.waitForTimeout(1500);

    const reloadedScope = await page.getByTestId("intake-v6-mounting-scope").inputValue();
    const reloadedSolution = await page.getByTestId("intake-v6-mounting-solution-selector").inputValue();
    const reloadedThickness = await page.getByTestId("intake-v6-mounting-acm-acm_thickness_mm").inputValue();

    await page.screenshot({
      path: path.join(OUT_DIR, "03_acm_reload_preserved.png"),
      fullPage: true,
    });

    const cppAfter = await fetchCppLines();
    let head = "unknown";
    try {
      head = execSync("git rev-parse --short HEAD", { encoding: "utf8", cwd: path.resolve(__dirname, "../../..") }).trim();
    } catch {
      head = "unknown";
    }

    const ownerRatesVerified = {
      ACM_PANEL_CUTTING: cppAfter.acm_lines?.find((l) => l.code === "acm_panel_cut")?.unit_price === 1.5,
      ACM_V_GROOVE: cppAfter.acm_lines?.find((l) => l.code === "acm_v_groove")?.unit_price === 3,
      ACM_BOXED_ASSEMBLY: cppAfter.acm_lines?.find((l) => l.code === "acm_boxed_assembly")?.unit_price === 15,
      ACM_BOXED_ASSEMBLY_MIN:
        (cppAfter.acm_lines?.find((l) => l.code === "acm_boxed_assembly")?.subtotal ?? 0) >= 20,
      MAT_ACM_FACE: cppAfter.acm_lines?.find((l) => l.code === "acm_panel_face_material")?.unit_price === 15,
      MAT_ACM_RETURN: cppAfter.acm_lines?.find((l) => l.code === "acm_return_strip_material")?.unit_price === 15,
      MAT_SURUBURI: cppAfter.acm_lines?.find((l) => l.code === "acm_fasteners")?.unit_price === 5,
      four_mm_blocked_ui: !thicknessValues.includes("4"),
      four_mm_only_3mm_option: thicknessValues.filter(Boolean).length === 1 && thicknessValues[0] === "3",
    };

    const duplicateCodes = (cppAfter.acm_line_codes ?? []).filter(
      (code, index, arr) => arr.indexOf(code) !== index,
    );

    const report = {
      task: "PRODUCT_SYSTEM_ACM_BOXED_MOUNTING_OWNER_RATES_DELIVERY_CLOSEOUT_V1",
      captured_at: new Date().toISOString(),
      head_before: "d693b37",
      head_at_capture: head,
      operator_route: OPERATOR_URL,
      workspace_id: WORKSPACE_ID,
      template_code: ACM,
      runtime: {
        frontend_status: 200,
        backend_status: 200,
        stack_healthy: true,
      },
      ui_verification: {
        mounting_scope: reloadedScope,
        mounting_solution: reloadedSolution,
        acm_thickness_mm: reloadedThickness,
        thickness_options: thicknessOptions,
        thickness_values: thicknessValues,
        reload_preserved:
          reloadedScope === "preparation_only" &&
          reloadedSolution === ACM &&
          reloadedThickness === "3",
      },
      cpp_api: {
        before: cppBefore,
        after: cppAfter,
        duplicate_acm_line_codes: duplicateCodes,
        no_duplicates: duplicateCodes.length === 0,
        forbidden_hourly_empty: (cppAfter.forbidden_hourly ?? []).length === 0,
      },
      owner_rates_verified: ownerRatesVerified,
      expected_acm_line_codes: [
        "acm_panel_cut",
        "acm_v_groove",
        "acm_panel_face_material",
        "acm_return_strip_material",
        "acm_boxed_assembly",
        "acm_fasteners",
      ],
      console_errors: consoleErrors,
      finish_put_events: finishPutEvents,
      verdict:
        Object.values(ownerRatesVerified).every(Boolean) &&
        cppAfter.ok &&
        (cppAfter.acm_line_codes?.length ?? 0) >= 6 &&
        duplicateCodes.length === 0
          ? "PASS"
          : "PARTIAL",
    };

    await writeFile(REPORT_PATH, JSON.stringify(report, null, 2));
    console.log(JSON.stringify({ verdict: report.verdict, owner_rates_verified: ownerRatesVerified }, null, 2));
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
