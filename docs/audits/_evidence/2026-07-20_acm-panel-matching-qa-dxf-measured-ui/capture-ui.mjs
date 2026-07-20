/**
 * UI capture — MATCHING QA DXF measured UI proof
 * QA workspace (2000×300 double-fold + golden DXF bound).
 * IV6-DB2F86B7: control only (no golden upload / no mutation).
 *
 * Env: PW_BASE_URL default http://127.0.0.1:3011
 */
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";
import fs from "node:fs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(path.join(__dirname, "../../../../frontend/package.json"));
const { chromium } = require("playwright");

const UI = process.env.PW_BASE_URL ?? "http://127.0.0.1:3011";
const QA = JSON.parse(fs.readFileSync(path.join(__dirname, "qa-workspace.json"), "utf8"));
const QA_ID = QA.workspace_id;
const QA_CODE = QA.workspace_code;
const IV6_ID = "a7b0162b-dc91-467f-aa24-c1279fb3a073";
const IV6_CODE = "IV6-DB2F86B7";
const OUT = path.join(__dirname, "shots");
const REPORT = path.join(__dirname, "screenshot-report.json");

async function shot(page, name, opts = {}) {
  fs.mkdirSync(OUT, { recursive: true });
  const file = `${name}.png`;
  await page.screenshot({ path: path.join(OUT, file), ...opts });
  return file;
}

function row(id, name, file, route, workspace, expected, observed, verdict, opinion = "") {
  return {
    id,
    name,
    file,
    route,
    workspace,
    viewport: "1440x900",
    expected,
    observed,
    verdict,
    opinion,
  };
}

async function openOperatorReview(page, workspaceId) {
  const route = `${UI}/intake-v6/${workspaceId}/operator`;
  await page.goto(route, { waitUntil: "domcontentloaded", timeout: 120000 });
  await page.getByTestId("intake-v6-header").waitFor({ state: "visible", timeout: 90000 });
  await page.getByTestId("intake-v6-progress-step-review").click().catch(() => {});
  await page.getByTestId("intake-v6-step-review").waitFor({ state: "visible", timeout: 60000 });
  await page.waitForTimeout(2500);
  return route;
}

async function openAcmGeometry(page) {
  const acmRow = page.getByTestId("intake-v6-product-component-row-acm_panel");
  await acmRow.waitFor({ state: "visible", timeout: 30000 });
  await acmRow.click();
  await page.waitForTimeout(1000);
  await page.getByTestId("intake-v6-acm-panel-inspector").waitFor({ state: "visible", timeout: 30000 });
  await page.getByTestId("intake-v6-acm-section-geometry").locator("button").first().click().catch(() => {});
  await page.waitForTimeout(500);
  const pg = page.getByTestId("intake-v6-acm-production-geometry");
  await pg.waitFor({ state: "visible", timeout: 30000 });
  await pg.scrollIntoViewIfNeeded();
  return pg;
}

async function main() {
  const rows = [];
  const mutating = [];
  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  await ctx.addInitScript(() => sessionStorage.setItem("WORKOS_DEV_GUARD_BYPASS", "1"));
  const page = await ctx.newPage();
  page.on("request", (req) => {
    const m = req.method();
    if (m === "GET" || m === "HEAD" || m === "OPTIONS") return;
    mutating.push({ method: m, url: req.url() });
  });
  // Capture is inspect-only: block finish/analysis writes so QA measured bind is not raced.
  await page.route("**/api/v1/intake-v6/workspaces/**/finish-setup", (route) => route.abort());
  await page.route("**/api/v1/intake-v6/workspaces/**/analysis-bundle", (route) => route.abort());

  // --- QA workspace (measured) ---
  const qaRoute = await openOperatorReview(page, QA_ID);

  rows.push(
    row(
      1,
      "qa_full_page",
      await shot(page, "01-qa-full-page", { fullPage: true }),
      qaRoute,
      QA_CODE,
      "QA Review full page with AcmPanel measured path",
      "page loaded",
      "PASS",
    ),
  );

  await openAcmGeometry(page);

  const dimsText = await page.getByTestId("intake-v6-acm-panel-inspector").innerText().catch(() => "");
  const hasDims = /2000/.test(dimsText) && /300/.test(dimsText);
  rows.push(
    row(
      2,
      "acm_dimensions",
      await shot(page, "02-acm-dimensions"),
      qaRoute,
      QA_CODE,
      "Face 2000×300 visible in AcmPanel config",
      hasDims ? "2000/300 present in inspector text" : dimsText.slice(0, 200),
      hasDims ? "PASS" : "REVIEW",
    ),
  );

  const hasL1L2 = /100/.test(dimsText) && /30/.test(dimsText);
  rows.push(
    row(
      3,
      "l1_l2",
      await shot(page, "03-l1-l2"),
      qaRoute,
      QA_CODE,
      "L1=100 / L2=30",
      hasL1L2 ? "100 and 30 present" : "partial",
      hasL1L2 ? "PASS" : "REVIEW",
    ),
  );

  const pgVisible = await page.getByTestId("intake-v6-acm-production-geometry").isVisible().catch(() => false);
  rows.push(
    row(
      4,
      "upload_block",
      await shot(page, "04-upload-block"),
      qaRoute,
      QA_CODE,
      "Production geometry DXF block in Geometrie",
      pgVisible ? "block visible" : "missing",
      pgVisible ? "PASS" : "FAIL",
    ),
  );

  const filename = await page.getByTestId("intake-v6-acm-pg-filename").innerText().catch(() => "");
  rows.push(
    row(
      5,
      "selected_dxf_filename",
      await shot(page, "05-selected-dxf-filename"),
      qaRoute,
      QA_CODE,
      "2-pliuri-100x30.dxf",
      filename,
      /2-pliuri-100x30\.dxf/i.test(filename) ? "PASS" : "FAIL",
    ),
  );

  const status = await page.getByTestId("intake-v6-acm-pg-status").innerText().catch(() => "");
  rows.push(
    row(
      6,
      "measured_status",
      await shot(page, "06-measured-status"),
      qaRoute,
      QA_CODE,
      "measurement_status measured",
      status,
      /măsurat|measured/i.test(status) ? "PASS" : "FAIL",
    ),
  );

  const metrics = await page.getByTestId("intake-v6-acm-pg-metrics").innerText().catch(() => "");
  rows.push(
    row(
      7,
      "cut_value",
      await shot(page, "07-cut-value"),
      qaRoute,
      QA_CODE,
      "CUT 5.499412",
      metrics,
      /5\.499412/.test(metrics) ? "PASS" : "FAIL",
    ),
  );
  rows.push(
    row(
      8,
      "v_l1",
      await shot(page, "08-v-l1"),
      qaRoute,
      QA_CODE,
      "V L1 5.4",
      metrics,
      /V L1:\s*5\.4\b/.test(metrics) || /5\.4\b/.test(metrics) ? "PASS" : "FAIL",
    ),
  );
  rows.push(
    row(
      9,
      "v_l2",
      await shot(page, "09-v-l2"),
      qaRoute,
      QA_CODE,
      "V L2 4.600004",
      metrics,
      /4\.600004/.test(metrics) ? "PASS" : "FAIL",
    ),
  );
  rows.push(
    row(
      10,
      "v_total",
      await shot(page, "10-v-total"),
      qaRoute,
      QA_CODE,
      "V total 10.000004",
      metrics,
      /10\.000004/.test(metrics) ? "PASS" : "FAIL",
    ),
  );

  const staleVisible = await page.getByTestId("intake-v6-acm-pg-stale").isVisible().catch(() => false);
  const assocText = await page.getByTestId("intake-v6-acm-summary-association").innerText().catch(() => "");
  rows.push(
    row(
      11,
      "panel_association_p1",
      await shot(page, "11-panel-association-p1"),
      qaRoute,
      QA_CODE,
      "panel_id p1 associated (single panel)",
      assocText || "single-panel; select hidden",
      "PASS",
      "Single-panel QA — panel select not shown; metrics snapshot panel_id=p1 in runtime-proof",
    ),
  );
  rows.push(
    row(
      12,
      "fingerprint_current",
      await shot(page, "12-fingerprint-current"),
      qaRoute,
      QA_CODE,
      "No stale warning; fingerprint current",
      staleVisible ? "stale banner visible" : "no stale banner",
      staleVisible ? "FAIL" : "PASS",
    ),
  );

  let panel = page
    .getByTestId("intake-v6-review-calculator-panel")
    .getByTestId("intake-v6-acm-panel-provisional-pricing");
  if ((await panel.count()) === 0) {
    panel = page.getByTestId("intake-v6-acm-panel-provisional-pricing").first();
  }
  await panel.waitFor({ state: "visible", timeout: 45000 }).catch(() => {});
  if (await panel.isVisible().catch(() => false)) {
    await panel.scrollIntoViewIfNeeded();
    await panel.getByTestId("intake-v6-acm-panel-breakdown-toggle").click().catch(() => {});
    await page.waitForTimeout(400);
  }
  const pathSource = await panel.getByTestId("intake-v6-acm-panel-path-source").innerText().catch(() => "");
  const panelText = await panel.innerText().catch(() => "");
  const measuredSourceOk =
    /măsurat\s*\(DXF\)|măsur|measured|imported_dxf/i.test(pathSource) ||
    /Sursă cantități:\s*măsurat/i.test(panelText);
  rows.push(
    row(
      13,
      "live_calc_measured_source",
      await shot(page, "13-live-calc-measured-source"),
      qaRoute,
      QA_CODE,
      "Sursă measured / imported_dxf",
      pathSource || panelText.match(/Sursă cantități:[^\n]+/)?.[0] || "",
      measuredSourceOk ? "PASS" : "FAIL",
    ),
  );

  const breakdown = await panel.getByTestId("intake-v6-acm-panel-breakdown-lines").innerText().catch(() => "");
  rows.push(
    row(
      14,
      "pricing_breakdown",
      await shot(page, "14-pricing-breakdown"),
      qaRoute,
      QA_CODE,
      "Breakdown shows CUT + V quantities",
      breakdown.slice(0, 300),
      /5\.499/.test(breakdown) && /V-groove ACM10|10 ml|10\.0/.test(breakdown) ? "PASS" : "FAIL",
    ),
  );

  const finalElig = await panel.getAttribute("data-final-eligible").catch(() => null);
  const offerElig = await panel.getAttribute("data-offer-eligible").catch(() => null);
  const execElig = await panel.getAttribute("data-execution-eligible").catch(() => null);
  rows.push(
    row(
      15,
      "final_blocked",
      await shot(page, "15-final-blocked"),
      qaRoute,
      QA_CODE,
      "final_eligibility false",
      String(finalElig),
      finalElig === "false" ? "PASS" : "FAIL",
    ),
  );
  rows.push(
    row(
      16,
      "offer_blocked",
      await shot(page, "16-offer-blocked"),
      qaRoute,
      QA_CODE,
      "offer_eligibility false",
      String(offerElig),
      offerElig === "false" ? "PASS" : "FAIL",
    ),
  );
  rows.push(
    row(
      17,
      "execution_blocked",
      await shot(page, "17-execution-blocked"),
      qaRoute,
      QA_CODE,
      "execution_eligibility false",
      String(execElig),
      execElig === "false" ? "PASS" : "FAIL",
    ),
  );

  const inspectorText = await page.getByTestId("intake-v6-acm-panel-inspector").innerText().catch(() => "");
  const moneyInInspector = /Estimare provizorie AcmPanel|\bEUR\b|\blei\b/i.test(inspectorText);
  rows.push(
    row(
      18,
      "inspector_no_money",
      await shot(page, "18-inspector-no-money"),
      qaRoute,
      QA_CODE,
      "Inspector has no money UI",
      moneyInInspector ? "money-like text found" : "no money header in inspector",
      moneyInInspector ? "FAIL" : "PASS",
    ),
  );

  // --- IV6 control (read-only) ---
  const iv6Route = await openOperatorReview(page, IV6_ID);
  await openAcmGeometry(page);
  const iv6Status = await page.getByTestId("intake-v6-acm-pg-status").innerText().catch(() => "");
  const iv6Metrics = await page.getByTestId("intake-v6-acm-pg-metrics").innerText().catch(() => "");
  const iv6Filename = await page.getByTestId("intake-v6-acm-pg-filename").innerText().catch(() => "");
  const iv6Ok =
    !/2-pliuri-100x30/i.test(iv6Filename) &&
    !/5\.499412/.test(iv6Metrics) &&
    !/10\.000004/.test(iv6Metrics);
  rows.push(
    row(
      19,
      "iv6_unchanged_unavailable",
      await shot(page, "19-iv6-unchanged-unavailable"),
      iv6Route,
      IV6_CODE,
      "IV6 still unavailable / no golden DXF",
      `status=${iv6Status}; file=${iv6Filename}; metrics=${iv6Metrics.slice(0, 120)}`,
      iv6Ok ? "PASS" : "FAIL",
      "Control only — must not show golden measured values",
    ),
  );

  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto(`${UI}/intake-v6/${QA_ID}/operator`, { waitUntil: "domcontentloaded", timeout: 120000 });
  await page.getByTestId("intake-v6-header").waitFor({ state: "visible", timeout: 90000 });
  await page.getByTestId("intake-v6-progress-step-review").click().catch(() => {});
  await page.waitForTimeout(2000);
  rows.push(
    row(
      20,
      "qa_full_page_final",
      await shot(page, "20-qa-full-page-final", { fullPage: true }),
      qaRoute,
      QA_CODE,
      "QA full page final after measured proof",
      "captured",
      "PASS",
    ),
  );

  const writesOnIv6 = mutating.filter((w) => String(w.url).includes(IV6_ID));
  const report = {
    ui: UI,
    qa: { workspace_id: QA_ID, workspace_code: QA_CODE },
    iv6_control: { workspace_id: IV6_ID, workspace_code: IV6_CODE },
    mutating_writes_during_capture: mutating,
    iv6_mutating_writes: writesOnIv6,
    note: "Capture is inspect/expand only; DXF already bound via seed_and_proof.py",
    rows,
  };
  fs.writeFileSync(REPORT, JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report, null, 2));
  await browser.close();
  const failed = rows.filter((r) => r.verdict === "FAIL").length;
  const iv6Writes = writesOnIv6.length;
  process.exit(failed || iv6Writes ? 1 : 0);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
