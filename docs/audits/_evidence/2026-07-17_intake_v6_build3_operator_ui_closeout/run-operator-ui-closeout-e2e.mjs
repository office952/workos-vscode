/**
 * Build 3 Operator UI Closeout — real UI E2E with gradi-curat.svg upload.
 * Binding: UI file input only (data-testid=intake-v6-svg-input). No API clone.
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
const HISTORICAL = "4888fddb-5d9f-46cb-9bcc-5dd3ed1263b1";
const TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2";

const SCENARIOS = [
  {
    id: "full_product",
    folder: "02_full_product",
    preset: "intake-v6-offer-scope-preset-full",
    mode: "full_product",
    sold: [],
  },
  {
    id: "face_only",
    folder: "03_face_only",
    preset: "intake-v6-offer-scope-preset-face",
    mode: "component_subset",
    sold: ["FACE"],
  },
  {
    id: "cant_only",
    folder: "04_cant_only",
    preset: "intake-v6-offer-scope-preset-cant",
    mode: "component_subset",
    sold: ["RETURN-CANT"],
  },
  {
    id: "face_cant",
    folder: "05_face_cant",
    preset: "intake-v6-offer-scope-preset-face-cant",
    mode: "component_subset",
    sold: ["FACE", "RETURN-CANT"],
  },
];

const evidence = {
  started_at: new Date().toISOString(),
  build: "BUILD3_OPERATOR_UI_CLOSEOUT",
  svg: {},
  system_status: {},
  scenarios: {},
  responsive: [],
  errors: [],
  verdict: null,
};

function log(step, data) {
  console.log(`[${step}]`, data.verdict || data.note || JSON.stringify(data).slice(0, 220));
}

async function apiGet(url) {
  const res = await fetch(url);
  const json = await res.json().catch(() => null);
  return { ok: res.ok, status: res.status, json };
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
  if (!workspaceId) {
    const row = page.locator('a[href*="/intake-v6/"]').first();
    if (await row.count()) {
      await row.click().catch(() => {});
      await waitReady(page);
      workspaceId = page.url().match(/intake-v6\/([0-9a-f-]{36})/i)?.[1] || null;
    }
  }
  if (!workspaceId || workspaceId === HISTORICAL) {
    throw new Error(`Could not create disposable workspace (got ${workspaceId})`);
  }
  return workspaceId;
}

async function uploadSvgViaUi(page, folder) {
  // Prefer operator panel input; preview-empty also mounts the same test id.
  const input = page
    .locator(
      '[data-testid="intake-v6-layers-operator-panel"] [data-testid="intake-v6-svg-input"], [data-testid="intake-v6-svg-input"]',
    )
    .first();
  await input.waitFor({ state: "attached", timeout: 30000 });
  await input.setInputFiles(SVG_PATH);
  await page.waitForTimeout(6000);
  await waitReady(page);
  await shot(page, folder, "02_svg_upload");
}

async function approveLayersAndComposition(page, folder) {
  for (const label of [
    "Confirmă toate",
    "Confirma toate",
    "Confirmă rolurile",
    "Acceptă propunerile",
    "Confirmă",
  ]) {
    const btn = page.locator(`button:has-text("${label}")`).first();
    if (await btn.count()) {
      await btn.click({ timeout: 4000 }).catch(() => {});
      await page.waitForTimeout(700);
    }
  }
  await shot(page, folder, "03_layers");
  for (const label of ["Confirmă compoziția", "Confirma compozitia", "Confirmă componentele"]) {
    const btn = page.locator(`button:has-text("${label}")`).first();
    if (await btn.count()) {
      await btn.click({ timeout: 4000 }).catch(() => {});
      await page.waitForTimeout(1000);
    }
  }
  await shot(page, folder, "04_components");
}

async function selectScopePreset(page, scenario, folder) {
  const preset = page.locator(`[data-testid="${scenario.preset}"]`);
  await preset.waitFor({ state: "visible", timeout: 20000 });
  await preset.click();
  await page.waitForTimeout(1500);
  await shot(page, folder, "05_scope");
}

async function goToReview(page, folder) {
  const footerNext = page.locator('[data-testid="intake-v6-footer-next"]');
  for (let i = 0; i < 8; i++) {
    const disabled = await footerNext.isDisabled().catch(() => true);
    if (!disabled) break;
    await page
      .locator('button:has-text("Confirmă toate"), button:has-text("Confirmă"), button:has-text("Acceptă")')
      .first()
      .click({ timeout: 3000 })
      .catch(() => {});
    await page.waitForTimeout(800);
  }
  if (await footerNext.count()) {
    await footerNext.click({ timeout: 15000 }).catch(() => {});
  }
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
  await page.waitForTimeout(1500);
  await shot(page, folder, "06_review");
}

function assertIsolation(id, probes) {
  const mats = probes.aggregate_materials || [];
  const cons = probes.consumable_keys || [];
  const cpp = probes.cpp_codes || [];
  const hasAdhesiveMat = mats.includes("MAT-ADEZIV-CANT-LITERE");
  const hasAdhesiveCons = cons.includes("adhesive_return_to_face");
  const hasFaceCpp = cpp.includes("debitare_fata");
  const hasCantCpp = cpp.some((c) => String(c).includes("modelare_cant"));
  const adhesiveCount = mats.filter((c) => c === "MAT-ADEZIV-CANT-LITERE").length;
  const adhesiveConsCount = cons.filter((k) => k === "adhesive_return_to_face").length;

  if (id === "full_product") {
    return { pass: hasAdhesiveCons || hasAdhesiveMat, hasAdhesiveMat, hasAdhesiveCons, hasFaceCpp, hasCantCpp };
  }
  if (id === "face_only") {
    return {
      pass: !hasAdhesiveMat && !hasAdhesiveCons && hasFaceCpp && !hasCantCpp,
      hasAdhesiveMat,
      hasAdhesiveCons,
      hasFaceCpp,
      hasCantCpp,
    };
  }
  if (id === "cant_only") {
    return {
      pass: !hasAdhesiveMat && !hasAdhesiveCons && !hasFaceCpp && hasCantCpp,
      hasAdhesiveMat,
      hasAdhesiveCons,
      hasFaceCpp,
      hasCantCpp,
    };
  }
  return {
    pass:
      (hasAdhesiveMat || hasAdhesiveCons) &&
      adhesiveCount <= 1 &&
      adhesiveConsCount <= 1 &&
      hasFaceCpp &&
      hasCantCpp,
    hasAdhesiveMat,
    hasAdhesiveCons,
    adhesiveCount,
    adhesiveConsCount,
    hasFaceCpp,
    hasCantCpp,
  };
}

async function probeApis(workspaceId) {
  const [ws, bd, agg, cpp, pd] = await Promise.all([
    apiGet(`${API}/intake-v6/workspaces/${workspaceId}`),
    apiGet(`${API}/intake-v6/workspaces/${workspaceId}/material-breakdown`),
    apiGet(`${API}/product-system/aggregate/${TEMPLATE}?workspace_id=${workspaceId}`),
    apiGet(`${API}/intake-v6/workspaces/${workspaceId}/priced-quote-dry-run`),
    apiGet(`${API}/product-system/product-definition/${TEMPLATE}?workspace_id=${workspaceId}`),
  ]);
  const analysis = ws.json?.payload?.svg_analysis_json || {};
  const layers = analysis.layers || analysis.layerSummaries || [];
  const colors = analysis.colors || analysis.colorSummaries || [];
  const contours =
    analysis.contour_count ||
    analysis.contourCount ||
    analysis.metrics?.contour_count ||
    analysis.document?.contourCount ||
    null;
  return {
    upload_method: "UI file input",
    file_name: ws.json?.payload?.svg_source?.file_name || null,
    file_hash: ws.json?.payload?.svg_source?.file_hash || null,
    layers_count: Array.isArray(layers) ? layers.length : null,
    colors_count: Array.isArray(colors) ? colors.length : null,
    contours,
    width_mm: analysis.document?.widthMm ?? analysis.document?.width_mm ?? null,
    height_mm: analysis.document?.heightMm ?? analysis.document?.height_mm ?? null,
    offer_scope: ws.json?.payload?.offer_scope || null,
    consumable_keys: (bd.json?.consumable_rows || []).map((r) => r.material_key),
    aggregate_materials: (agg.json?.materials || []).map((m) => m.material_code).filter(Boolean),
    cpp_codes: (cpp.json?.commercial_line_items || []).map((l) => l.code || l.line_code).filter(Boolean),
    pd_ok: pd.ok,
    debitare_fata_qty: (cpp.json?.commercial_line_items || []).find((l) => l.code === "debitare_fata")
      ?.quantity,
  };
}

async function runScenario(browser, scenario) {
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();
  const folder = scenario.folder;
  const result = { id: scenario.id, folder, errors: [] };
  try {
    const workspaceId = await createDisposableWorkspace(page);
    result.workspace_id = workspaceId;
    result.url = page.url();
    await shot(page, folder, "01_workspace");

    // System status proof early
    const banner = page.locator('[data-testid="environment-banner"]');
    await banner.waitFor({ state: "attached", timeout: 15000 }).catch(() => {});
    result.system_status = {
      presentation: await banner.getAttribute("data-presentation").catch(() => null),
      severity: await banner.getAttribute("data-severity").catch(() => null),
      chip_text: await page.locator('[data-testid="environment-banner-main"]').innerText().catch(() => null),
      in_topbar: await page
        .locator('[data-testid="workos-desktop-topbar"] [data-testid="environment-banner"]')
        .count()
        .then((n) => n > 0),
      full_width_strip_absent:
        (await page.locator('[data-testid="environment-banner"]').evaluate((el) => {
          const rect = el.getBoundingClientRect();
          const parent = el.closest('[data-testid="workos-desktop-topbar"]');
          return Boolean(parent) && rect.width < window.innerWidth * 0.5;
        }).catch(() => false)),
    };
    await shot(page, "01_runtime_status", `${scenario.id}_status`);

    // Ensure layers step
    await page
      .locator('[data-testid="intake-v6-progress-step-layers"], button:has-text("Straturi")')
      .first()
      .click({ timeout: 5000 })
      .catch(() => {});
    await page.waitForTimeout(800);

    await uploadSvgViaUi(page, folder);
    await approveLayersAndComposition(page, folder);
    await selectScopePreset(page, scenario, folder);
    await goToReview(page, folder);

    const scopeSummary = await page
      .locator('[data-testid="intake-v6-review-offer-scope-summary"]')
      .innerText()
      .catch(() => "");
    result.review_scope_summary = scopeSummary;
    await shot(page, folder, "07_live_calc");

    // Sticky footer authority proof (Review): workspace sticky, save non-sticky
    const stickyProof = await page.evaluate(() => {
      const ws = document.querySelector('[data-testid="intake-v6-operator-workspace-footer"]');
      const save = document.querySelector('[data-testid="intake-v6-review-save-footer"]');
      const wsClass = ws?.className || "";
      const saveClass = save?.className || "";
      return {
        workspace_sticky: wsClass.includes("sticky") && wsClass.includes("bottom-0"),
        save_relative: saveClass.includes("relative") && !saveClass.includes("sticky"),
        save_present: Boolean(save),
      };
    });
    result.sticky_footer = stickyProof;
    if (scenario.id === "full_product") {
      await shot(page, "06_sticky_footer", "review_footers");
    }

    // Save
    await page
      .locator('[data-testid="intake-v6-save"], button:has-text("Salvează"), button:has-text("Salveaza")')
      .first()
      .click({ timeout: 5000 })
      .catch(() => {});
    await page.waitForTimeout(1200);

    // Leave / return / hard refresh
    await page.goto(`${BASE}/intake-v6/operator`, { waitUntil: "domcontentloaded" });
    await page.goto(`${BASE}/intake-v6/${workspaceId}/operator`, {
      waitUntil: "domcontentloaded",
      timeout: 60000,
    });
    await waitReady(page);
    await page.reload({ waitUntil: "domcontentloaded" });
    await waitReady(page);
    await shot(page, folder, "08_hard_refresh");

    const probes = await probeApis(workspaceId);
    result.probes = probes;
    const payloadDir = path.join(EVIDENCE, "08_payloads");
    fs.mkdirSync(payloadDir, { recursive: true });
    fs.writeFileSync(
      path.join(payloadDir, `${scenario.id}.json`),
      JSON.stringify({ workspaceId, probes }, null, 2),
    );
    result.isolation = assertIsolation(scenario.id, probes);
    result.upload_ok =
      probes.file_name === "gradi-curat.svg" &&
      Boolean(probes.file_hash) &&
      result.system_status.presentation === "compact" &&
      result.system_status.in_topbar === true;
    result.verdict =
      result.upload_ok && result.isolation.pass && result.system_status.full_width_strip_absent
        ? "PASS"
        : "FAIL";
    log(`scenario_${scenario.id}`, {
      workspace_id: workspaceId,
      verdict: result.verdict,
      note: JSON.stringify(result.isolation),
    });
  } catch (err) {
    result.errors.push(String(err));
    result.verdict = "FAIL";
    evidence.errors.push({ scenario: scenario.id, error: String(err) });
    log(`scenario_${scenario.id}`, { verdict: "FAIL", note: String(err) });
  } finally {
    await context.close();
  }
  return result;
}

async function main() {
  const svgBytes = fs.readFileSync(SVG_PATH);
  evidence.svg = {
    path: SVG_PATH,
    size: svgBytes.length,
    hash: crypto.createHash("sha256").update(svgBytes).digest("hex"),
    upload_method_required: "UI file input data-testid=intake-v6-svg-input",
  };

  const browser = await chromium.launch({ headless: true });
  try {
    // Banner smoke on operator landing
    const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await ctx.newPage();
    await page.goto(`${BASE}/intake-v6/operator`, { waitUntil: "domcontentloaded" });
    await waitReady(page);
    evidence.system_status.landing = {
      presentation: await page
        .locator('[data-testid="environment-banner"]')
        .getAttribute("data-presentation")
        .catch(() => null),
      in_topbar: (await page.locator('[data-testid="workos-desktop-topbar"] [data-testid="environment-banner"]').count()) > 0,
      screenshot: await shot(page, "01_runtime_status", "landing_compact"),
      chip_text: await page
        .locator('[data-testid="environment-banner-main"]')
        .innerText()
        .catch(() => null),
      severity: await page
        .locator('[data-testid="environment-banner"]')
        .getAttribute("data-severity")
        .catch(() => null),
    };
    // Open details + Control Center link
    await page.locator('[data-testid="environment-banner-details-toggle"]').click().catch(() => {});
    await page.waitForTimeout(500);
    evidence.system_status.details_accessible =
      (await page
        .locator(
          '[data-testid="runtime-status-details"], [data-testid="environment-banner-details-panel"]',
        )
        .count()) > 0;
    evidence.system_status.control_center_link =
      (await page.locator('[data-testid="environment-banner-control-center-link"]').count()) > 0;
    evidence.system_status.control_center_text = await page
      .locator('[data-testid="environment-banner-control-center-link"]')
      .innerText()
      .catch(() => null);
    await shot(page, "01_runtime_status", "details_open");
    await ctx.close();
    log("system_status", evidence.system_status.landing);

    for (const scenario of SCENARIOS) {
      evidence.scenarios[scenario.id] = await runScenario(browser, scenario);
    }

    // Responsive on last PASS workspace (cant_only preferred)
    const uiWs =
      evidence.scenarios.cant_only?.workspace_id ||
      evidence.scenarios.full_product?.workspace_id;
    if (uiWs) {
      const rctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
      const rpage = await rctx.newPage();
      await rpage.goto(`${BASE}/intake-v6/${uiWs}/operator`, { waitUntil: "domcontentloaded" });
      await waitReady(rpage);
      for (const [w, h, name] of [
        [1440, 900, "desktop"],
        [1280, 800, "laptop"],
        [1024, 768, "small_laptop"],
        [768, 1024, "tablet"],
      ]) {
        await rpage.setViewportSize({ width: w, height: h });
        await rpage.waitForTimeout(400);
        const scroll = await rpage.evaluate(() => ({
          scrollWidth: document.documentElement.scrollWidth,
          clientWidth: document.documentElement.clientWidth,
        }));
        const noHScroll = scroll.scrollWidth <= scroll.clientWidth + 2;
        const bannerInTopbar =
          (await rpage
            .locator('[data-testid="workos-desktop-topbar"] [data-testid="environment-banner"]')
            .count()) > 0;
        evidence.responsive.push({
          name,
          w,
          h,
          noHScroll,
          bannerInTopbar,
          screenshot: await shot(rpage, "07_responsive", name),
          verdict: noHScroll && bannerInTopbar ? "PASS" : "FAIL",
        });
        log(`responsive_${name}`, {
          noHScroll,
          bannerInTopbar,
          verdict: noHScroll && bannerInTopbar ? "PASS" : "FAIL",
        });
      }
      await rctx.close();
    }
  } finally {
    await browser.close();
  }

  const scenarioFails = Object.values(evidence.scenarios).filter((s) => s.verdict !== "PASS").length;
  const responsiveFails = evidence.responsive.filter((r) => r.verdict !== "PASS").length;
  const stickyFails = Object.values(evidence.scenarios).filter(
    (s) => s.sticky_footer && (!s.sticky_footer.workspace_sticky || !s.sticky_footer.save_relative),
  ).length;
  const statusOk =
    evidence.system_status.landing?.presentation === "compact" &&
    evidence.system_status.landing?.in_topbar === true &&
    evidence.system_status.details_accessible === true &&
    evidence.system_status.control_center_link === true;

  if (scenarioFails === 0 && responsiveFails === 0 && stickyFails === 0 && statusOk) {
    evidence.verdict = "BUILD3_OPERATOR_UI_CLOSEOUT_COMPLETE_WITH_GUARDS";
  } else if (!statusOk) {
    evidence.verdict = "RUNTIME_STATUS_PRESENTATION_FAILED";
  } else if (stickyFails > 0) {
    evidence.verdict = "STICKY_LAYOUT_FAILED";
  } else if (responsiveFails > 0) {
    evidence.verdict = "UI_RESPONSIVE_FAILED";
  } else if (evidence.scenarios.full_product?.verdict !== "PASS") {
    evidence.verdict = "FULL_PRODUCT_UI_REGRESSION";
  } else if (
    Object.values(evidence.scenarios).some(
      (s) => s.upload_ok === false || s.probes?.file_name !== "gradi-curat.svg",
    )
  ) {
    evidence.verdict = "REAL_SVG_UI_PROOF_FAILED";
  } else {
    evidence.verdict = "SUBSET_UI_REGRESSION";
  }

  evidence.finished_at = new Date().toISOString();
  fs.writeFileSync(path.join(EVIDENCE, "evidence.json"), JSON.stringify(evidence, null, 2));
  console.log("VERDICT", evidence.verdict);
  console.log(
    "SCENARIOS",
    Object.fromEntries(
      Object.entries(evidence.scenarios).map(([k, v]) => [k, { id: v.workspace_id, verdict: v.verdict }]),
    ),
  );
  if (evidence.verdict !== "BUILD3_OPERATOR_UI_CLOSEOUT_COMPLETE_WITH_GUARDS") process.exitCode = 1;
}

main().catch((err) => {
  evidence.errors.push(String(err));
  evidence.verdict = "TOOLING_BLOCKED";
  evidence.finished_at = new Date().toISOString();
  fs.writeFileSync(path.join(EVIDENCE, "evidence.json"), JSON.stringify(evidence, null, 2));
  console.error(err);
  process.exit(2);
});
