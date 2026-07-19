/**
 * Desktop presentation reset V1 — before baselines (audit pack) + after live shots.
 * FE :3000 · proxy BACKEND_PORT=8003 · BE :8003
 */
import fs from "fs";
import path from "path";
import { createRequire } from "module";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(path.join(__dirname, "../../../frontend/package.json"));
const { chromium } = require("playwright");

const UI = process.env.PW_BASE_URL ?? "http://127.0.0.1:3000";
const API = `${UI}/api/v1/intake-v6`;
const OUT = path.join(__dirname, "runtime");
const SHOTS = path.join(__dirname, "screenshots");
const BEFORE_SRC = path.join(__dirname, "../intake-v6-desktop-ui-reset-2026-07-19/screenshots");
const FIX = "C:/Users/offic/Desktop/fisiere-teste-svg";

fs.mkdirSync(OUT, { recursive: true });
fs.mkdirSync(SHOTS, { recursive: true });

function copyBeforeBaselines() {
  const map = [
    ["02_finisaje_top.png", "01_before_finisaje_first_paint.png"],
    ["03_finisaje_letter_expanded.png", "02_before_finisaje_cant.png"],
    ["04_iluminare_top.png", "03_before_iluminare_first_paint.png"],
    ["05_iluminare_calculated_results.png", "04_before_iluminare_results.png"],
    ["06_montaj_top.png", "05_before_montaj_acm.png"],
    ["08_fundal_carcasa.png", "06_before_fundal_carcasa.png"],
    ["09_support_structure.png", "07_before_segmented.png"],
    ["07_montaj_commercial.png", "08_before_commercial_inactive.png"],
    ["07_montaj_commercial.png", "09_before_commercial_active.png"],
    ["10_montaj_avansat.png", "10_before_montaj_avansat.png"],
    ["15_confirmare.png", "11_before_confirmare_blocked.png"],
    ["15_confirmare.png", "12_before_confirmare_ready.png"],
    ["13_pricing_rail.png", "13_before_pricing_compact.png"],
    ["11_warnings_near_bottom.png", "14_before_diagnostic.png"],
    ["14_footer.png", "16_before_footer.png"],
    ["02_finisaje_top.png", "17_before_full_1440.png"],
    ["17_narrow_desktop.png", "18_before_narrow_1100.png"],
  ];
  for (const [srcName, destName] of map) {
    const src = path.join(BEFORE_SRC, srcName);
    if (fs.existsSync(src)) fs.copyFileSync(src, path.join(SHOTS, destName));
  }
}

async function createWs(title) {
  const r = await fetch(`${API}/workspaces`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      title,
      selected_template_code: "TPL-VOLUMETRIC-LETTERS_v2",
      analyzer_mode: "analyzer_first",
    }),
  });
  if (!r.ok) throw new Error(`create ${r.status}`);
  return r.json();
}

async function clientUpload(page, filePath) {
  const chooserPromise = page.waitForEvent("filechooser", { timeout: 15000 }).catch(() => null);
  await page.getByRole("button", { name: /Încarcă SVG/i }).first().click({ force: true }).catch(() => null);
  const chooser = await chooserPromise;
  if (chooser) await chooser.setFiles(filePath);
  else {
    const input = page.locator('input[type="file"]').first();
    if ((await input.count()) > 0) await input.setInputFiles(filePath);
  }
  await page.waitForTimeout(7000);
}

async function confirmRoles(page) {
  const support = page.locator('select[data-testid="intake-v6-layer-role-pseudo:fill-c5c6c6"]');
  if ((await support.count()) > 0) {
    await support.selectOption("support_panel");
    await page.waitForTimeout(3000);
  }
  const face = page.locator('select[data-testid="intake-v6-layer-role-pseudo:fill-e31e24"]');
  if ((await face.count()) > 0) {
    await face.selectOption("face");
    await page.waitForTimeout(1500);
  }
  const confirmAll = page.getByRole("button", { name: /Confirmă toate|Confirmă rolurile|Acceptă propunerile/i }).first();
  if ((await confirmAll.count()) > 0) await confirmAll.click({ force: true }).catch(() => null);
  else {
    const selects = page.locator('select[data-testid^="intake-v6-layer-role-"]');
    const n = await selects.count();
    for (let i = 0; i < n; i++) {
      const sel = selects.nth(i);
      const val = await sel.inputValue().catch(() => null);
      if (val) await sel.selectOption(val).catch(() => null);
    }
  }
  await page.waitForTimeout(2000);
  const next = page.getByRole("button", { name: /Continuă|Următor/i }).first();
  if ((await next.count()) > 0) await next.click({ force: true }).catch(() => null);
  await page.waitForTimeout(1500);
}

async function goReview(page, wsId) {
  await page.goto(`${UI}/intake-v6/${wsId}/operator`, { waitUntil: "domcontentloaded", timeout: 120000 });
  await page.waitForTimeout(1200);
  await page.locator('[data-testid="intake-v6-progress-step-review"]').click({ force: true });
  await page.waitForSelector('[data-testid="intake-v6-review-tabs"]', { timeout: 30000 });
  await page.waitForTimeout(1500);
}

async function openTab(page, tabId, panelId) {
  await page.locator(`[data-testid="intake-v6-review-tab-${tabId}"]`).click({ force: true });
  await page.waitForSelector(`[data-testid="${panelId}"]`, { timeout: 15000 });
  await page.waitForTimeout(800);
}

async function shot(page, name, full = true) {
  const dest = path.join(SHOTS, name);
  await page.screenshot({ path: dest, fullPage: full });
  console.log("shot", name, fs.statSync(dest).size);
}

async function probeOperatorBoundary(page) {
  return page.evaluate(() => {
    const text = document.body.innerText;
    const compositionText =
      document.querySelector('[data-testid="intake-v6-product-composition-panel"]')?.textContent ?? "";
    const diagOpen =
      document
        .querySelector('[data-testid="intake-v6-review-technical-details"]')
        ?.getAttribute("data-expanded") === "true";
    return {
      href: location.href,
      viewport: { w: innerWidth, h: innerHeight },
      hasBlockerBanner: Boolean(
        document.querySelector('[data-testid="intake-v6-review-operator-blocker-banner"]'),
      ),
      footerHintBanner: /Următorul pas este în footer/i.test(text),
      rawTplOnCompositionL1: /TPL-[A-Z0-9-]+/i.test(compositionText),
      productTruthVisible: /Product Truth Promotion Planner|Form System Backbone/i.test(text),
      writeFlagsVisible: /product_truth_write|pricing_write|task_graph_write/i.test(text),
      diagnosticExpanded: diagOpen,
      confirmFirstPaint: Boolean(document.querySelector('[data-testid="intake-v6-confirm-first-paint"]')),
      fundalFirst: document
        .querySelector('[data-testid="intake-v6-review-tab-panel-montaj"]')
        ?.getAttribute("data-fundal-first"),
      iluminareContractDup: Boolean(
        document.querySelector('[data-testid="intake-v6-review-section-iluminare"]'),
      ),
      lightingSection: Boolean(
        document.querySelector('[data-testid="intake-v6-review-lighting-section"]'),
      ),
      montajPanel: Boolean(document.querySelector('[data-testid="intake-v6-review-tab-panel-montaj"]')),
      finisajePanel: Boolean(document.querySelector('[data-testid="intake-v6-review-tab-panel-finisaje"]')),
      rezultatComercial: /Rezultat comercial/i.test(text),
      footerNext: /Următorul pas:/i.test(text),
    };
  });
}

async function main() {
  copyBeforeBaselines();
  const browser = await chromium.launch({ headless: true });
  const fileAcm = path.join(FIX, "litere-cu-fundal-acm-segmentat.svg");
  const fileSimple = path.join(FIX, "litere-vol-1-layer.svg");
  const summary = { ui: UI, at: new Date().toISOString(), cases: [] };

  {
    const ws = await createWs(`presentation-reset-acm-${Date.now()}`);
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
    await page.goto(`${UI}/intake-v6/${ws.id}/operator`, { waitUntil: "domcontentloaded", timeout: 120000 });
    await page.waitForTimeout(1200);
    await clientUpload(page, fileAcm);
    await confirmRoles(page);
    await goReview(page, ws.id);

    await openTab(page, "finisaje", "intake-v6-review-tab-panel-finisaje");
    await shot(page, "01_after_finisaje_first_paint.png");
    await shot(page, "17_after_full_1440.png");

    const letter = page.locator('[data-testid^="intake-v6-letter-group-"]').first();
    if ((await letter.count()) > 0) {
      await letter.click({ force: true }).catch(() => null);
      await page.waitForTimeout(500);
    }
    await shot(page, "02_after_finisaje_cant.png");

    const pricing = page.locator('[data-testid="intake-v6-review-calculator-panel"]');
    if ((await pricing.count()) > 0) {
      await pricing.screenshot({ path: path.join(SHOTS, "13_after_pricing_compact.png") });
      console.log("shot 13_after_pricing_compact.png", fs.statSync(path.join(SHOTS, "13_after_pricing_compact.png")).size);
    }

    await page.screenshot({
      path: path.join(SHOTS, "16_after_footer.png"),
      clip: { x: 0, y: 820, width: 1440, height: 180 },
    });
    console.log("shot 16_after_footer.png");

    await openTab(page, "iluminare", "intake-v6-review-tab-panel-iluminare");
    await shot(page, "03_after_iluminare_first_paint.png");
    const results = page.locator('[data-testid="intake-v6-lighting-results"]');
    if ((await results.count()) > 0) {
      await results.screenshot({ path: path.join(SHOTS, "04_after_iluminare_results.png") });
      console.log("shot 04_after_iluminare_results.png");
    } else {
      await shot(page, "04_after_iluminare_results.png");
    }

    await openTab(page, "montaj", "intake-v6-review-tab-panel-montaj");
    await shot(page, "05_after_montaj_acm.png");

    const fundal = page.locator('[data-testid="intake-v6-fundal-carcasa-cluster"]');
    if ((await fundal.count()) > 0) {
      await fundal.locator("button").first().click({ force: true }).catch(() => null);
      await page.waitForTimeout(500);
      await fundal.screenshot({ path: path.join(SHOTS, "06_after_fundal_carcasa.png") });
      await fundal.screenshot({ path: path.join(SHOTS, "07_after_segmented.png") });
      console.log("shot fundal/segmented");
    } else {
      await shot(page, "06_after_fundal_carcasa.png");
      await shot(page, "07_after_segmented.png");
    }

    const commercial = page.locator('[data-testid="intake-v6-montaj-commercial-cluster"]');
    if ((await commercial.count()) > 0) {
      await commercial.screenshot({ path: path.join(SHOTS, "08_after_commercial_inactive.png") });
      await commercial.locator("button").first().click({ force: true }).catch(() => null);
      await page.waitForTimeout(400);
      await commercial.screenshot({ path: path.join(SHOTS, "09_after_commercial_active.png") });
      console.log("shot commercial");
    } else {
      await shot(page, "08_after_commercial_inactive.png");
      await shot(page, "09_after_commercial_active.png");
    }

    const advanced = page.locator('[data-testid="intake-v6-montaj-advanced-cluster"]');
    if ((await advanced.count()) > 0) {
      // capture collapsed first
      await advanced.screenshot({ path: path.join(SHOTS, "10_after_montaj_avansat.png") });
      console.log("shot avansat collapsed");
    } else {
      await shot(page, "10_after_montaj_avansat.png");
    }

    // Diagnostic collapsed / expanded on Montaj (bottom of page)
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(400);
    await shot(page, "14_after_diagnostic_collapsed.png", false);
    const diagToggle = page.locator('[data-testid="intake-v6-review-technical-details-toggle"]');
    if ((await diagToggle.count()) > 0) {
      await diagToggle.click({ force: true });
      await page.waitForTimeout(800);
      await shot(page, "15_after_diagnostic_expanded.png", false);
      await diagToggle.click({ force: true }).catch(() => null);
      await page.waitForTimeout(300);
    } else {
      await shot(page, "15_after_diagnostic_expanded.png", false);
    }

    // Confirmare blocked first paint (composition still unconfirmed)
    await goReview(page, ws.id);
    await page.locator('[data-testid="intake-v6-progress-step-confirm"]').click({ force: true }).catch(() => null);
    await page.waitForTimeout(800);
    await page.getByRole("button", { name: /Continuă la Confirmare/i }).first().click({ force: true }).catch(() => null);
    await page.waitForSelector('[data-testid="intake-v6-confirm-first-paint"]', { timeout: 20000 }).catch(() => null);
    await page.waitForTimeout(1200);
    await shot(page, "11_after_confirmare_blocked.png");

    // Confirm composition then Confirmare again for "ready-ish" first paint
    await goReview(page, ws.id);
    await page.locator('[data-testid="intake-v6-confirm-product-composition"]').click({ force: true }).catch(() => null);
    await page.waitForTimeout(2500);
    await page.locator('[data-testid="intake-v6-progress-step-confirm"]').click({ force: true }).catch(() => null);
    await page.waitForTimeout(800);
    await page.getByRole("button", { name: /Continuă la Confirmare/i }).first().click({ force: true }).catch(() => null);
    await page.waitForSelector('[data-testid="intake-v6-confirm-first-paint"]', { timeout: 20000 }).catch(() => null);
    await page.waitForTimeout(1500);
    await shot(page, "12_after_confirmare_ready.png");

    // Reload review
    await goReview(page, ws.id);
    await page.reload({ waitUntil: "domcontentloaded" });
    await page.waitForTimeout(3000);
    await page.locator('[data-testid="intake-v6-progress-step-review"]').click({ force: true }).catch(() => null);
    await page.waitForSelector('[data-testid="intake-v6-review-tabs"]', { timeout: 30000 }).catch(() => null);
    await page.waitForTimeout(1500);
    await openTab(page, "finisaje", "intake-v6-review-tab-panel-finisaje").catch(() => null);
    await shot(page, "19_after_reloaded.png");

    await openTab(page, "montaj", "intake-v6-review-tab-panel-montaj").catch(() => null);
    const montajProbe = await probeOperatorBoundary(page);

    await page.setViewportSize({ width: 1100, height: 900 });
    await page.waitForTimeout(500);
    await openTab(page, "finisaje", "intake-v6-review-tab-panel-finisaje").catch(() => null);
    await shot(page, "18_after_narrow_1100.png");

    const caseAcm = {
      id: "acm_presentation_reset",
      workspace_id: ws.id,
      workspace_code: ws.workspace_code,
      probe: montajProbe,
    };
    fs.writeFileSync(path.join(OUT, "acm_presentation_probe.json"), JSON.stringify(caseAcm, null, 2));
    summary.cases.push(caseAcm);
    await page.close();
  }

  if (fs.existsSync(fileSimple)) {
    const ws = await createWs(`presentation-reset-letters-${Date.now()}`);
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
    await page.goto(`${UI}/intake-v6/${ws.id}/operator`, { waitUntil: "domcontentloaded", timeout: 120000 });
    await clientUpload(page, fileSimple);
    const face = page.locator('select[data-testid^="intake-v6-layer-role-"]').first();
    if ((await face.count()) > 0) {
      await face.selectOption("face").catch(() => null);
      await page.waitForTimeout(1500);
    }
    await confirmRoles(page);
    await goReview(page, ws.id);
    await openTab(page, "finisaje", "intake-v6-review-tab-panel-finisaje");
    await shot(page, "20_after_simple_letters_finisaje.png");
    summary.cases.push({
      id: "simple_letters",
      workspace_id: ws.id,
      probe: await probeOperatorBoundary(page),
    });
    await page.close();
  }

  await browser.close();
  fs.writeFileSync(path.join(OUT, "presentation_reset_summary.json"), JSON.stringify(summary, null, 2));
  console.log(JSON.stringify(summary, null, 2));
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
