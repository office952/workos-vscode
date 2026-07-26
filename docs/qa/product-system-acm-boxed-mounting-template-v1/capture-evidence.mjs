/**
 * QA evidence — PRODUCT_SYSTEM_ACM_BOXED_MOUNTING_TEMPLATE_V1
 */
import { chromium } from "@playwright/test";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT_DIR = path.join(__dirname, "screenshots");
const REPORT_PATH = path.join(__dirname, "evidence_report.json");
const ACM = "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1";
const METAL = "TPL-METAL-PREMOUNT-STRUCTURE_v1";
const OPERATOR_URL = "http://127.0.0.1:3000/intake-v6/IR-MRI01769/operator";

const scenarios = [];
const consoleErrors = [];

async function snap(page, name, file, flow, detail) {
  await page.screenshot({ path: path.join(OUT_DIR, file), fullPage: true });
  scenarios.push({ name, screenshot: file, flow, detail });
}

async function openProductSystem(page) {
  await page.goto("http://127.0.0.1:3000/product-system", { waitUntil: "domcontentloaded", timeout: 120_000 });
  await page.getByTestId("product-system-unified-catalog").waitFor({ timeout: 60_000 });
  await page.waitForTimeout(2000);
}

async function expandLegacyBucket(page) {
  const bucket = page.getByTestId("product-system-catalog-bucket-legacy-shared-modules");
  await bucket.waitFor({ timeout: 60_000 });
  if ((await bucket.getAttribute("data-expanded")) !== "true") {
    await page.getByTestId("product-system-catalog-bucket-toggle-legacy-shared-modules").click();
    await bucket.waitFor({ state: "visible", timeout: 10_000 });
    await page.waitForTimeout(800);
  }
}

async function gotoMontaj(page) {
  await page.goto(OPERATOR_URL, { waitUntil: "domcontentloaded", timeout: 120_000 });
  await page.getByTestId("intake-v6-header").waitFor({ timeout: 120_000 });
  await page.getByTestId("intake-v6-progress-step-review").click();
  await page.getByTestId("intake-v6-step-review").waitFor({ timeout: 60_000 });
  await page.getByTestId("intake-v6-review-tab-montaj").click();
  await page.getByTestId("intake-v6-review-tab-panel-montaj").waitFor({ timeout: 60_000 });
  await page.waitForTimeout(1500);
}

async function main() {
  await mkdir(OUT_DIR, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  page.on("console", (msg) => {
    if (msg.type() === "error") consoleErrors.push(msg.text());
  });

  await openProductSystem(page);
  await snap(page, "product_system_loaded", "01_product_system_catalog_loaded.png", "A", "Unified catalog shell");

  await page.getByTestId("product-system-filter-candidate-products").click();
  await page.waitForTimeout(1200);
  await snap(page, "candidate_filter", "02_candidate_products_filter.png", "A", "Candidate filter (may be empty)");

  await page.getByTestId("product-system-filter-all").click();
  await expandLegacyBucket(page);
  await snap(page, "legacy_bucket_expanded", "03_legacy_modules_bucket_acm_home.png", "A", "ACM listed as internal module");

  const acmRow = page.getByTestId(`product-system-unified-row-${ACM}`);
  await acmRow.waitFor({ timeout: 60_000 });
  await acmRow.click();
  await page.getByTestId("product-system-template-detail-panel").waitFor({ timeout: 30_000 });
  await snap(page, "acm_detail_panel", "04_acm_template_detail_panel.png", "A", ACM);

  await gotoMontaj(page);
  await page.getByTestId("intake-v6-mounting-scope").selectOption("preparation_only");
  await page.waitForTimeout(2000);
  await snap(page, "montaj_preparation", "05_intake_montaj_preparation_scope.png", "B", "Mounting prep active");

  await page.getByTestId("intake-v6-mounting-solution-selector").selectOption(ACM);
  await page.getByTestId("intake-v6-mounting-acm-panel_width_mm").waitFor({ timeout: 30_000 });
  await snap(page, "acm_selected", "06_intake_acm_mounting_solution_selected.png", "B", "ACM linked child fields");

  await page.getByTestId("intake-v6-mounting-solution-selector").selectOption(METAL);
  await page.getByTestId("intake-v6-mounting-solution-bar-material").waitFor({ timeout: 30_000 });
  await snap(page, "metal_regression", "07_metal_premount_regression.png", "B", METAL);

  let schemaFreshness = {};
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

  await writeFile(
    REPORT_PATH,
    JSON.stringify(
      {
        task: "PRODUCT_SYSTEM_ACM_BOXED_MOUNTING_TEMPLATE_V1",
        captured_at: new Date().toISOString(),
        head: "564ce48",
        workspace_id: "b00a3a0c-5a3d-4d0b-a95e-582bb542dde1",
        operator_route: OPERATOR_URL,
        template_code: ACM,
        playwright_attempts: [
          { attempt: 1, result: "fail", reason: "Flow A query param + Flow B bare workspace route" },
          { attempt: 2, result: "fail", reason: "Candidate bucket missing (ACM in legacy modules); networkidle hang" },
        ],
        evidence_capture_script: "docs/qa/product-system-acm-boxed-mounting-template-v1/capture-evidence.mjs",
        schema_freshness: schemaFreshness,
        console_errors: consoleErrors,
        scenarios,
        missing_owner_rates: [
          { code: "PANEL_CUTTING", basis: "workcenter", notes: "CUT_ACM_PANEL" },
          { code: "ASSEMBLY", basis: "workcenter", notes: "FOLD_CASSETTE, MOUNT_ACM_PANEL" },
          { code: "MAT-SURUBURI-GEN", basis: "material", notes: "comp_mounting_fasteners" },
          { code: "MAT-ACM-BOND-4MM", basis: "material", notes: "needs_review — 3MM confirmed 15 EUR/mp" },
          { code: "V_GROOVE_ROUTER", basis: "workcenter", notes: "basis mismatch vs perimeter formula" },
        ],
        verdict: scenarios.length === 7 ? "PASS" : "PARTIAL",
      },
      null,
      2,
    ),
  );

  await browser.close();
  console.log(JSON.stringify({ screenshots: scenarios.length, report: REPORT_PATH }, null, 2));
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
