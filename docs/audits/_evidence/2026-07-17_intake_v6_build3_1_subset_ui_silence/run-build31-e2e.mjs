/**
 * Build 3.1 — subset UI silence E2E with real gradi-curat.svg via UI.
 */
import { createRequire } from "node:module";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import crypto from "node:crypto";

const require = createRequire(path.join("C:\\w\\psiso\\frontend", "package.json"));
const { chromium } = require("playwright");

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const EVIDENCE = __dirname;
const SVG_PATH = "C:\\Users\\offic\\Desktop\\fisiere-teste-svg\\gradi-curat.svg";
const BASE = "http://127.0.0.1:3000";
const API = `${BASE}/api/v1`;
const TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2";
const HISTORICAL = "4888fddb-5d9f-46cb-9bcc-5dd3ed1263b1";

const SCENARIOS = [
  { id: "full_product", folder: "01_full", preset: "intake-v6-offer-scope-preset-full", expectTabs: ["finisaje", "iluminare", "montaj"] },
  { id: "face_only", folder: "02_face", preset: "intake-v6-offer-scope-preset-face", expectTabs: ["finisaje"] },
  { id: "cant_only", folder: "03_cant", preset: "intake-v6-offer-scope-preset-cant", expectTabs: ["finisaje"] },
  { id: "face_cant", folder: "04_face_cant", preset: "intake-v6-offer-scope-preset-face-cant", expectTabs: ["finisaje"] },
];

const report = {
  started_at: new Date().toISOString(),
  build: "BUILD3_1_SUBSET_UI_SILENCE",
  svg: {},
  scenarios: {},
  scope_switch: {},
  responsive: [],
  errors: [],
  verdict: null,
};

function log(step, data) {
  console.log(`[${step}]`, typeof data === "string" ? data : JSON.stringify(data).slice(0, 260));
}

async function apiGet(url) {
  const res = await fetch(url);
  return { ok: res.ok, json: await res.json().catch(() => null) };
}

async function waitReady(page) {
  await page.waitForLoadState("networkidle", { timeout: 45000 }).catch(() => {});
}

async function shot(page, folder, name) {
  const dir = path.join(EVIDENCE, folder);
  fs.mkdirSync(dir, { recursive: true });
  const p = path.join(dir, `${name}.png`);
  await page.screenshot({ path: p, fullPage: true });
  return p;
}

async function createDisposableWorkspace(page) {
  await page.goto(`${BASE}/intake-v6/operator`, { waitUntil: "domcontentloaded", timeout: 60000 });
  await waitReady(page);
  const newBtn = page
    .locator(
      '[data-testid="intake-v6-new-request"], button:has-text("Cerere nouă"), button:has-text("Cerere noua"), button:has-text("Workspace nou")',
    )
    .first();
  if (await newBtn.count()) {
    await newBtn.click({ timeout: 10000 }).catch(() => {});
    await waitReady(page);
  }
  const confirm = page
    .locator(
      'button:has-text("Creează"), button:has-text("Creeaza"), button:has-text("Continuă"), button:has-text("Continua"), [data-testid="intake-v6-create-workspace"]',
    )
    .first();
  if (await confirm.count()) {
    await confirm.click({ timeout: 8000 }).catch(() => {});
    await waitReady(page);
  }
  await page.waitForTimeout(1200);
  let workspaceId = page.url().match(/intake-v6\/([0-9a-f-]{36})/i)?.[1] || null;
  if (!workspaceId || workspaceId === HISTORICAL) {
    throw new Error(`Could not create disposable workspace (got ${workspaceId})`);
  }
  return workspaceId;
}

async function uploadSvg(page) {
  const input = page.locator('[data-testid="intake-v6-svg-input"]').first();
  await input.waitFor({ state: "attached", timeout: 30000 });
  await input.setInputFiles(SVG_PATH);
  await page.waitForTimeout(6000);
  await waitReady(page);
}

async function approveFlow(page) {
  for (const label of ["Confirmă toate", "Confirma toate", "Confirmă", "Acceptă propunerile"]) {
    const btn = page.locator(`button:has-text("${label}")`).first();
    if (await btn.count()) {
      await btn.click({ timeout: 4000 }).catch(() => {});
      await page.waitForTimeout(600);
    }
  }
  for (const label of ["Confirmă compoziția", "Confirma compozitia", "Confirmă componentele"]) {
    const btn = page.locator(`button:has-text("${label}")`).first();
    if (await btn.count()) {
      await btn.click({ timeout: 4000 }).catch(() => {});
      await page.waitForTimeout(800);
    }
  }
}

async function selectPreset(page, testId) {
  await page.locator(`[data-testid="${testId}"]`).click({ timeout: 20000 });
  await page.waitForTimeout(1200);
}

async function goReview(page) {
  const footerNext = page.locator('[data-testid="intake-v6-footer-next"]');
  for (let i = 0; i < 8; i++) {
    if (!(await footerNext.isDisabled().catch(() => true))) break;
    await page
      .locator('button:has-text("Confirmă toate"), button:has-text("Confirmă")')
      .first()
      .click({ timeout: 3000 })
      .catch(() => {});
    await page.waitForTimeout(700);
  }
  await footerNext.click({ timeout: 15000 }).catch(() => {});
  await page
    .waitForFunction(
      () =>
        document
          .querySelector('[data-testid="intake-v6-workspace-main"]')
          ?.getAttribute("data-intake-v6-step") === "review",
      { timeout: 60000 },
    )
    .catch(() => {});
  await page.locator('[data-testid="intake-v6-progress-step-review"]').click({ timeout: 5000 }).catch(() => {});
  await page.waitForTimeout(1200);
}

async function goConfirm(page) {
  await page.locator('[data-testid="intake-v6-progress-step-confirm"]').click({ timeout: 8000 }).catch(() => {});
  await page.locator('[data-testid="intake-v6-footer-next"]').click({ timeout: 8000 }).catch(() => {});
  await page.waitForTimeout(1500);
}

async function probe(workspaceId) {
  const [ws, handoff, agg, cpp] = await Promise.all([
    apiGet(`${API}/intake-v6/workspaces/${workspaceId}`),
    apiGet(`${API}/intake-v6/workspaces/${workspaceId}/quote-handoff-preview`),
    apiGet(`${API}/product-system/aggregate/${TEMPLATE}?workspace_id=${workspaceId}`),
    apiGet(`${API}/intake-v6/workspaces/${workspaceId}/priced-quote-dry-run`),
  ]);
  const mats = (agg.json?.materials || []).map((m) => m.material_code).filter(Boolean);
  const fatals = handoff.json?.fatal_blockers || handoff.json?.blockers || [];
  const fatalStr = JSON.stringify(fatals);
  return {
    file_name: ws.json?.payload?.svg_source?.file_name || null,
    offer_scope: ws.json?.payload?.offer_scope || null,
    readiness: ws.json?.readiness_status || null,
    has_mounting_fatal: /MOUNTING_SOLUTION/i.test(fatalStr),
    has_adhesive: mats.includes("MAT-ADEZIV-CANT-LITERE"),
    adhesive_count: mats.filter((c) => c === "MAT-ADEZIV-CANT-LITERE").length,
    cpp_codes: (cpp.json?.commercial_line_items || []).map((l) => l.code || l.line_code).filter(Boolean),
    fatals,
  };
}

async function uiTabIds(page) {
  return page.evaluate(() =>
    [...document.querySelectorAll('[data-testid="intake-v6-review-tabs"] [role="tab"]')]
      .map((el) => (el.getAttribute("data-testid") || "").replace("intake-v6-review-tab-", ""))
      .filter((id) => id === "finisaje" || id === "iluminare" || id === "montaj"),
  );
}

async function runScenario(browser, scenario) {
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();
  const out = { id: scenario.id, folder: scenario.folder, errors: [] };
  try {
    const workspaceId = await createDisposableWorkspace(page);
    out.workspace_id = workspaceId;
    await page
      .locator('[data-testid="intake-v6-progress-step-layers"], button:has-text("Straturi")')
      .first()
      .click()
      .catch(() => {});
    await uploadSvg(page);
    await approveFlow(page);
    await selectPreset(page, scenario.preset);
    await goReview(page);
    await shot(page, scenario.folder, "configurare");
    out.tabs = await uiTabIds(page);
    out.tabs_pass = JSON.stringify(out.tabs) === JSON.stringify(scenario.expectTabs);
    out.body_has_iluminare_tab = out.tabs.includes("iluminare");
    out.body_has_montaj_tab = out.tabs.includes("montaj");
    const bannerText = await page
      .locator('[data-testid="intake-v6-operator-blocker-banner"], [data-testid="intake-v6-footer-issues"]')
      .innerText()
      .catch(() => "");
    out.mounting_blocker_ui = /montaj|MOUNTING_SOLUTION|șablon montaj|sablon montaj/i.test(bannerText);
    await goConfirm(page);
    await shot(page, scenario.folder, "confirmare");
    out.confirm_hint = await page
      .locator('[data-testid="intake-v6-final-configuration-summary"]')
      .innerText()
      .catch(() => "");
    out.confirm_scope = await page
      .locator('[data-testid="intake-v6-review-offer-scope-summary"]')
      .innerText()
      .catch(() => "");
    out.confirm_full_product_ish =
      scenario.id !== "full_product" &&
      /Toate componentele produsului|Iluminare|Montaj/.test(out.confirm_hint) &&
      !/Nu sunt incluse/.test(out.confirm_scope);
    out.probes = await probe(workspaceId);

    // save / leave / return / hard refresh
    await page
      .locator('[data-testid="intake-v6-save"], button:has-text("Salvează"), button:has-text("Salveaza")')
      .first()
      .click({ timeout: 4000 })
      .catch(() => {});
    await page.goto(`${BASE}/intake-v6/operator`, { waitUntil: "domcontentloaded" });
    await page.goto(`${BASE}/intake-v6/${workspaceId}/operator`, { waitUntil: "domcontentloaded" });
    await waitReady(page);
    await page.reload({ waitUntil: "domcontentloaded" });
    await waitReady(page);
    await page.locator('[data-testid="intake-v6-progress-step-review"]').click().catch(() => {});
    await page.waitForTimeout(800);
    out.tabs_after_refresh = await uiTabIds(page);
    out.refresh_tabs_pass = JSON.stringify(out.tabs_after_refresh) === JSON.stringify(scenario.expectTabs);

    const isolation =
      scenario.id === "full_product"
        ? out.probes.has_adhesive
        : scenario.id === "face_cant"
          ? out.probes.has_adhesive && out.probes.adhesive_count <= 1
          : !out.probes.has_adhesive;

    const mountingOk =
      scenario.id === "full_product"
        ? true // full product may still require mounting readiness
        : !out.probes.has_mounting_fatal && !out.mounting_blocker_ui;
    out.verdict =
      out.tabs_pass &&
      out.refresh_tabs_pass &&
      mountingOk &&
      isolation &&
      out.probes.file_name === "gradi-curat.svg" &&
      (scenario.id === "full_product"
        ? out.body_has_iluminare_tab && out.body_has_montaj_tab
        : !out.body_has_iluminare_tab && !out.body_has_montaj_tab)
        ? "PASS"
        : "FAIL";
    log(scenario.id, { verdict: out.verdict, tabs: out.tabs, mounting_fatal: out.probes.has_mounting_fatal });
  } catch (e) {
    out.errors.push(String(e));
    out.verdict = "FAIL";
    report.errors.push({ id: scenario.id, error: String(e) });
    log(scenario.id, String(e));
  } finally {
    await ctx.close();
  }
  return out;
}

async function main() {
  const svgBytes = fs.readFileSync(SVG_PATH);
  report.svg = {
    path: SVG_PATH,
    hash: crypto.createHash("sha256").update(svgBytes).digest("hex"),
  };
  const browser = await chromium.launch({ headless: true });
  try {
    for (const scenario of SCENARIOS) {
      report.scenarios[scenario.id] = await runScenario(browser, scenario);
    }

    // Scope switching on a fresh CANT workspace if available
    const cantWs = report.scenarios.cant_only?.workspace_id;
    if (cantWs) {
      const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
      const page = await ctx.newPage();
      await page.goto(`${BASE}/intake-v6/${cantWs}/operator`, { waitUntil: "domcontentloaded" });
      await waitReady(page);
      await page.locator('[data-testid="intake-v6-progress-step-layers"]').click().catch(() => {});
      await selectPreset(page, "intake-v6-offer-scope-preset-full");
      await goReview(page);
      const fullTabs = await uiTabIds(page);
      await page.locator('[data-testid="intake-v6-progress-step-layers"]').click().catch(() => {});
      await selectPreset(page, "intake-v6-offer-scope-preset-cant");
      await goReview(page);
      const cantTabs = await uiTabIds(page);
      report.scope_switch = {
        full_tabs: fullTabs,
        cant_tabs: cantTabs,
        pass:
          JSON.stringify(fullTabs) === JSON.stringify(["finisaje", "iluminare", "montaj"]) &&
          JSON.stringify(cantTabs) === JSON.stringify(["finisaje"]),
      };
      await shot(page, "05_scope_switch", "cant_after_full");
      await ctx.close();
      log("scope_switch", report.scope_switch);
    }

    const uiWs = report.scenarios.cant_only?.workspace_id;
    if (uiWs) {
      const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
      const page = await ctx.newPage();
      await page.goto(`${BASE}/intake-v6/${uiWs}/operator`, { waitUntil: "domcontentloaded" });
      await waitReady(page);
      await page.locator('[data-testid="intake-v6-progress-step-review"]').click().catch(() => {});
      for (const [w, h, name] of [
        [1440, 900, "desktop"],
        [1280, 800, "laptop"],
        [1024, 768, "small_laptop"],
        [768, 1024, "tablet"],
      ]) {
        await page.setViewportSize({ width: w, height: h });
        await page.waitForTimeout(300);
        const ok = await page.evaluate(() => {
          const hScroll = document.documentElement.scrollWidth > document.documentElement.clientWidth + 2;
          const tabs = [...document.querySelectorAll('[data-testid="intake-v6-review-tabs"] [role="tab"]')]
            .map((el) => (el.getAttribute("data-testid") || "").replace("intake-v6-review-tab-", ""))
            .filter((id) => id === "finisaje" || id === "iluminare" || id === "montaj");
          return { hScroll, tabs };
        });
        report.responsive.push({
          name,
          w,
          h,
          noHScroll: !ok.hScroll,
          tabs: ok.tabs,
          screenshot: await shot(page, "06_responsive", name),
          verdict:
            !ok.hScroll &&
            ok.tabs.includes("finisaje") &&
            !ok.tabs.includes("iluminare") &&
            !ok.tabs.includes("montaj")
              ? "PASS"
              : "FAIL",
        });
      }
      await ctx.close();
    }
  } finally {
    await browser.close();
  }

  const fails = Object.values(report.scenarios).filter((s) => s.verdict !== "PASS").length;
  const respFails = report.responsive.filter((r) => r.verdict !== "PASS").length;
  if (fails === 0 && respFails === 0 && report.scope_switch.pass !== false) {
    report.verdict = "BUILD3_1_SUBSET_UI_ALIGNMENT_COMPLETE_WITH_GUARDS";
  } else if (report.scenarios.cant_only?.verdict !== "PASS") {
    report.verdict = "CANT_UI_STILL_LEAKING";
  } else if (report.scenarios.full_product?.verdict !== "PASS") {
    report.verdict = "FULL_PRODUCT_UI_REGRESSION";
  } else {
    report.verdict = "FAILED";
  }
  report.finished_at = new Date().toISOString();
  fs.mkdirSync(EVIDENCE, { recursive: true });
  fs.writeFileSync(path.join(EVIDENCE, "evidence.json"), JSON.stringify(report, null, 2));
  console.log("VERDICT", report.verdict);
  console.log(
    "SCENARIOS",
    Object.fromEntries(Object.entries(report.scenarios).map(([k, v]) => [k, { id: v.workspace_id, verdict: v.verdict, tabs: v.tabs }])),
  );
  if (!String(report.verdict).includes("COMPLETE")) process.exitCode = 1;
}

main().catch((err) => {
  report.errors.push(String(err));
  report.verdict = "TOOLING_BLOCKED";
  fs.writeFileSync(path.join(EVIDENCE, "evidence.json"), JSON.stringify(report, null, 2));
  console.error(err);
  process.exit(2);
});
