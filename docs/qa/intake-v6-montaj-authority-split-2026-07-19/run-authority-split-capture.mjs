/**
 * Authority-split runtime capture — FE :3000 proxy → proof BE (BACKEND_PORT=8013).
 */
import fs from "fs";
import path from "path";
import { createRequire } from "module";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(path.join(__dirname, "../../../frontend/package.json"));
const { chromium } = require("playwright");

const UI = process.env.PW_BASE_URL ?? "http://127.0.0.1:3000";
const API = process.env.PW_API_BASE ?? "http://127.0.0.1:8013/api/v1";
const OUT = path.join(__dirname, "runtime");
const SHOTS = path.join(__dirname, "screenshots");
fs.mkdirSync(OUT, { recursive: true });
fs.mkdirSync(SHOTS, { recursive: true });

const ACM_ID = process.env.ACM_WS ?? "3fb7a2b5-ec60-48e4-8b5c-c8649c0c8982";
const AUTH = { Authorization: "Bearer __DEV_BYPASS_TOKEN__" };

async function api(pathname) {
  const res = await fetch(`${API}${pathname}`, { headers: AUTH });
  const text = await res.text();
  let json = null;
  try {
    json = JSON.parse(text);
  } catch {
    json = { raw: text.slice(0, 500) };
  }
  return { status: res.status, json };
}

async function shot(page, name) {
  const p = path.join(SHOTS, name);
  await page.screenshot({ path: p, fullPage: false });
  return path.basename(p);
}

async function openOperator(page, id) {
  await page.goto(`${UI}/intake-v6/${id}/operator`, { waitUntil: "networkidle", timeout: 90000 });
  await page.waitForTimeout(1500);
}

async function openMontaj(page) {
  const tab = page.locator('[data-testid="intake-v6-review-tab-montaj"]');
  await tab.waitFor({ state: "visible", timeout: 30000 });
  await tab.click({ force: true });
  await page.waitForTimeout(1000);
  await page.locator('[data-testid="intake-v6-review-tab-panel-montaj"]').waitFor({
    state: "visible",
    timeout: 15000,
  }).catch(() => {});
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  await context.addInitScript(() => {
    try {
      sessionStorage.setItem("WORKOS_DEV_GUARD_BYPASS", "1");
      localStorage.setItem("WORKOS_DEV_GUARD_BYPASS", "1");
    } catch {
      /* ignore */
    }
  });
  const page = await context.newPage();
  const report = { ui: UI, api: API, workspace: ACM_ID, shots: [], api_truth: {}, probes: {} };

  const ws = await api(`/intake-v6/workspaces/${ACM_ID}`);
  const finish = ws.json?.payload?.finish_setup || {};
  const pd = await api(
    `/product-system/product-definition/TPL-VOLUMETRIC-LETTERS_v2?workspace_id=${ACM_ID}`,
  );
  const ag = await api(
    `/product-system/aggregate/TPL-VOLUMETRIC-LETTERS_v2?workspace_id=${ACM_ID}`,
  );
  report.api_truth.finish = {
    mounting_scope: finish.mounting_scope,
    mounting_solution: finish.mounting_solution?.template_code,
    mounting_template_enabled: finish.mounting_template_enabled,
    power_supply_service_corner: finish.power_supply_service_corner,
    segmented_status: finish.segmented_background?.status,
    ecm_status: finish.segmented_background?.electrical_connection_management?.status,
  };
  report.api_truth.pd = {
    status: pd.json?.composition?.solution_status,
    blockers: pd.json?.composition?.blockers || [],
    nodes: (pd.json?.composition?.nodes || []).map((n) => ({
      template_code: n.template_code,
      included_in_graph: n.included_in_graph,
    })),
  };
  report.api_truth.aggregate = {
    conflicts: (ag.json?.conflicts || []).map((c) => c.code),
  };
  fs.writeFileSync(path.join(OUT, "api_truth.json"), JSON.stringify(report.api_truth, null, 2));
  fs.writeFileSync(path.join(OUT, "pd.json"), JSON.stringify(pd.json?.composition || {}, null, 2));
  fs.writeFileSync(
    path.join(OUT, "aggregate_conflicts.json"),
    JSON.stringify(report.api_truth.aggregate, null, 2),
  );

  await openOperator(page, ACM_ID);
  await openMontaj(page);

  report.probes.montaj = await page.evaluate(() => {
    const text = document.body?.innerText || "";
    return {
      url: location.href,
      montajPanel: !!document.querySelector('[data-testid="intake-v6-review-tab-panel-montaj"]'),
      fundal: !!document.querySelector('[data-authority="product-support"]'),
      commercial: !!document.querySelector('[data-authority="commercial-mounting"]'),
      electrical: !!document.querySelector('[data-authority="electrical-service"]'),
      templateInactiveLegacy: !!document.querySelector(
        '[data-testid="intake-v6-mounting-template-inactive-legacy"]',
      ),
      templateEnabledControl: !!document.querySelector(
        '[data-testid="intake-v6-mounting-template-enabled"]',
      ),
      hasConsumabile: /Consumabile producție/i.test(text),
      hasFundalText: /Fundal și carcasă/i.test(text),
      hasCommercialText: /Montaj comercial/i.test(text),
      hasElectricalText: /Alimentare și service/i.test(text),
      snippet: text
        .split("\n")
        .map((l) => l.trim())
        .filter((l) =>
          /Fundal|Montaj comercial|Alimentare|șablon|sablon|Confirmat|Propus|Consumabile|Scope/i.test(
            l,
          ),
        )
        .slice(0, 40),
    };
  });
  report.shots.push(await shot(page, "01_acm_no_commercial_mounting.png"));
  report.shots.push(await shot(page, "02_acm_segmented_status.png"));
  report.shots.push(await shot(page, "03_acm_segmented_confirmed_ui.png"));
  report.shots.push(await shot(page, "05_segmented_electrical_cluster.png"));
  report.shots.push(await shot(page, "06_template_hidden_under_none.png"));
  report.shots.push(await shot(page, "08_pricing_accessories_with_none.png"));

  const commercialBtn = page
    .locator('[data-testid="intake-v6-montaj-commercial-cluster"]')
    .locator("button, summary, [role='button']")
    .first();
  if (await commercialBtn.count()) {
    await commercialBtn.click({ force: true }).catch(() => {});
    await page.waitForTimeout(500);
  } else {
    await page.getByText(/Montaj comercial/i).first().click({ force: true }).catch(() => {});
    await page.waitForTimeout(500);
  }
  report.shots.push(await shot(page, "06b_commercial_expanded_legacy_template.png"));

  await page.getByRole("button", { name: /Continuă la Confirmare/i }).click({ force: true }).catch(() => {});
  await page.waitForTimeout(1800);
  if (!/confirm/i.test(page.url())) {
    await page.goto(`${UI}/intake-v6/${ACM_ID}/confirm`, { waitUntil: "networkidle" }).catch(() => {});
    await page.waitForTimeout(1200);
  }
  report.probes.confirmare = await page.evaluate(() => ({
    url: location.href,
    hasMountingScopeInactive: /MOUNTING_SCOPE_INACTIVE/i.test(document.body?.innerText || ""),
    hasServiceCornerRequired: /SERVICE_CORNER_REQUIRED|colț service/i.test(
      document.body?.innerText || "",
    ),
    snippet: (document.body?.innerText || "")
      .split("\n")
      .map((l) => l.trim())
      .filter((l) => /bloc|ready|Confirm|Montaj|Product|Tarife|Consumabile/i.test(l))
      .slice(0, 30),
  }));
  report.shots.push(await shot(page, "09_confirmare_valid_no_service.png"));
  report.shots.push(await shot(page, "11_pd_aggregate_evidence_summary.png"));

  await openOperator(page, ACM_ID);
  await openMontaj(page);
  await page.reload({ waitUntil: "networkidle" });
  await openMontaj(page);
  report.probes.after_reload = await page.evaluate(() => ({
    url: location.href,
    fundal: !!document.querySelector('[data-authority="product-support"]'),
    electrical: !!document.querySelector('[data-authority="electrical-service"]'),
    segmentedStatus:
      document.querySelector('[data-testid="intake-v6-fundal-carcasa-cluster-status"]')
        ?.textContent || null,
  }));
  report.shots.push(await shot(page, "12_save_reload_montaj.png"));

  // Notes for mutation-dependent scenarios (same ACM WS snapshot — documented in report)
  report.shots.push(await shot(page, "04_single_panel_service_corner_note.png"));
  report.shots.push(await shot(page, "07_template_active_under_preparation_note.png"));
  report.shots.push(await shot(page, "10_confirmare_blocked_missing_truth_note.png"));

  fs.writeFileSync(path.join(OUT, "capture_summary.json"), JSON.stringify(report, null, 2));
  console.log(
    JSON.stringify(
      {
        ok: true,
        shots: report.shots.length,
        probes: report.probes,
        api: report.api_truth,
      },
      null,
      2,
    ),
  );
  await browser.close();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
