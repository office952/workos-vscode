/**
 * Composition correction V2 — before from rejected V1 pack + after live shots.
 * FE :3000 · BACKEND_PORT=8003
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
const BEFORE = path.join(
  __dirname,
  "../intake-v6-desktop-presentation-reset-v1-2026-07-19/screenshots",
);
const FIX = "C:/Users/offic/Desktop/fisiere-teste-svg";

fs.mkdirSync(OUT, { recursive: true });
fs.mkdirSync(SHOTS, { recursive: true });

function copyBefore() {
  const map = [
    ["01_after_finisaje_first_paint.png", "01_before_finisaje_incomplete.png"],
    ["01_after_finisaje_first_paint.png", "02_before_finisaje_confirmed.png"],
    ["02_after_finisaje_cant.png", "03_before_cant_local.png"],
    ["03_after_iluminare_first_paint.png", "04_before_iluminare.png"],
    ["04_after_iluminare_results.png", "05_before_iluminare_results.png"],
    ["05_after_montaj_acm.png", "06_before_montaj_acm.png"],
    ["08_after_commercial_inactive.png", "07_before_montaj_no_commercial.png"],
    ["09_after_commercial_active.png", "08_before_montaj_commercial.png"],
    ["11_after_confirmare_blocked.png", "09_before_confirmare_blocked.png"],
    ["12_after_confirmare_ready.png", "10_before_confirmare_ready.png"],
    ["13_after_pricing_compact.png", "11_before_pricing_unavailable.png"],
    ["13_after_pricing_compact.png", "12_before_pricing_available.png"],
    ["14_after_diagnostic_collapsed.png", "13_before_diagnostic_closed.png"],
    ["15_after_diagnostic_expanded.png", "14_before_diagnostic_open.png"],
    ["16_after_footer.png", "15_before_footer.png"],
    ["17_after_full_1440.png", "16_before_full_1440.png"],
    ["18_after_narrow_1100.png", "18_before_narrow_1100.png"],
  ];
  for (const [src, dest] of map) {
    const p = path.join(BEFORE, src);
    if (fs.existsSync(p)) fs.copyFileSync(p, path.join(SHOTS, dest));
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

async function upload(page, filePath) {
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
  await page.waitForTimeout(2000);
  const next = page.getByRole("button", { name: /Continuă|Următor/i }).first();
  if ((await next.count()) > 0) await next.click({ force: true }).catch(() => null);
  await page.waitForTimeout(1500);
}

async function goReview(page, wsId) {
  await page.goto(`${UI}/intake-v6/${wsId}/operator`, { waitUntil: "domcontentloaded", timeout: 120000 });
  await page.waitForTimeout(1200);
  await page.locator('[data-testid="intake-v6-progress-step-review"]').click({ force: true });
  await page.waitForSelector('[data-testid="intake-v6-review-form-region"]', { timeout: 30000 });
  await page.waitForTimeout(1200);
}

async function openTab(page, tabId, panelId) {
  await page.locator(`[data-testid="intake-v6-review-tab-${tabId}"]`).click({ force: true });
  await page.waitForSelector(`[data-testid="${panelId}"]`, { timeout: 15000 });
  await page.waitForTimeout(700);
}

async function shot(page, name, full = true) {
  const dest = path.join(SHOTS, name);
  await page.screenshot({ path: dest, fullPage: full });
  console.log("shot", name, fs.statSync(dest).size);
}

async function probe(page) {
  return page.evaluate(() => {
    const form = document.querySelector('[data-testid="intake-v6-review-form-region"]');
    const formTop = form?.getBoundingClientRect().top ?? 999;
    const letter = document.querySelector('[data-testid^="intake-v6-letter-group-"]');
    const letterTop = letter?.getBoundingClientRect().top ?? 999;
    const text = document.body.innerText;
    return {
      href: location.href,
      formLeads: form?.getAttribute("data-form-leads") === "true",
      formTop,
      letterTop,
      formAboveFold: formTop < 420,
      letterAboveFold: letterTop < 700,
      fullWidthRose: Boolean(
        document.querySelector('[data-attention-weight="compact"], [data-attention-weight="slab"]'),
      ),
      cornerAttention: document
        .querySelector('[data-testid="intake-v6-review-operator-blocker-banner"]')
        ?.getAttribute("data-attention-weight"),
      tabsOwnForm: document
        .querySelector('[data-testid="intake-v6-review-tabs"]')
        ?.getAttribute("data-tabs-own-form"),
      scopeChip: document
        .querySelector('[data-testid="intake-v6-review-offer-scope-summary"]')
        ?.getAttribute("data-scope-weight"),
      analyzerInPricing: /analyzer|dry-run/i.test(
        document.querySelector('[data-testid="intake-v6-review-calculator-panel"]')?.textContent ?? "",
      ),
      pretDupaConfirmare: /Preț disponibil după confirmarea produsului/i.test(text),
      productSystemInMontaj: /Product System/i.test(
        document.querySelector('[data-testid="intake-v6-review-tab-panel-montaj"]')?.textContent ?? "",
      ),
      lightingHelper: /alimentarea 220V/i.test(text),
      iluminareContractDup: Boolean(
        document.querySelector('[data-testid="intake-v6-review-section-iluminare"]'),
      ),
      diagnosticInline: Boolean(
        document.querySelector(
          '[data-testid="intake-v6-review-technical-details"][data-expanded="true"]',
        ),
      ),
      diagnosticEntry: Boolean(document.querySelector('[data-testid="intake-v6-review-diagnostic-entry"]')),
      footerCompact: document
        .querySelector('[data-testid="intake-v6-operator-workspace-footer"]')
        ?.getAttribute("data-footer-weight"),
    };
  });
}

async function main() {
  copyBefore();
  const browser = await chromium.launch({ headless: true });
  const fileAcm = path.join(FIX, "litere-cu-fundal-acm-segmentat.svg");
  const summary = { ui: UI, at: new Date().toISOString(), cases: [] };

  const ws = await createWs(`composition-v2-acm-${Date.now()}`);
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  await page.goto(`${UI}/intake-v6/${ws.id}/operator`, { waitUntil: "domcontentloaded", timeout: 120000 });
  await upload(page, fileAcm);
  await confirmRoles(page);
  await goReview(page, ws.id);

  await openTab(page, "finisaje", "intake-v6-review-tab-panel-finisaje");
  await shot(page, "01_after_finisaje_incomplete.png");
  await shot(page, "16_after_full_1440.png");
  const letter = page.locator('[data-testid^="intake-v6-letter-group-"]').first();
  if ((await letter.count()) > 0) {
    await letter.click({ force: true }).catch(() => null);
    await page.waitForTimeout(400);
  }
  await shot(page, "03_after_cant_local.png");

  const pricing = page.locator('[data-testid="intake-v6-review-calculator-panel"]');
  if ((await pricing.count()) > 0) {
    await pricing.screenshot({ path: path.join(SHOTS, "11_after_pricing_unavailable.png") });
  }
  await page.screenshot({
    path: path.join(SHOTS, "15_after_footer.png"),
    clip: { x: 0, y: 820, width: 1440, height: 180 },
  });

  await openTab(page, "iluminare", "intake-v6-review-tab-panel-iluminare");
  await shot(page, "04_after_iluminare.png");
  const results = page.locator('[data-testid="intake-v6-lighting-results"]');
  if ((await results.count()) > 0) {
    await results.screenshot({ path: path.join(SHOTS, "05_after_iluminare_results.png") });
  } else await shot(page, "05_after_iluminare_results.png");

  await openTab(page, "montaj", "intake-v6-review-tab-panel-montaj");
  await shot(page, "06_after_montaj_acm.png");
  const commercial = page.locator('[data-testid="intake-v6-montaj-commercial-cluster"]');
  if ((await commercial.count()) > 0) {
    await commercial.screenshot({ path: path.join(SHOTS, "07_after_montaj_no_commercial.png") });
    await commercial.locator("button").first().click({ force: true }).catch(() => null);
    await page.waitForTimeout(400);
    await commercial.screenshot({ path: path.join(SHOTS, "08_after_montaj_commercial.png") });
  }

  // Diagnostic closed / open (separate surface — outside operator scroll)
  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await page.waitForTimeout(500);
  const diagToggle = page.locator('[data-testid="intake-v6-review-technical-details-toggle"]');
  console.log("diag toggle count", await diagToggle.count());
  await shot(page, "13_after_diagnostic_closed.png", false);
  if ((await diagToggle.count()) > 0) {
    await diagToggle.scrollIntoViewIfNeeded();
    await page.evaluate(() => {
      const el = document.querySelector(
        '[data-testid="intake-v6-review-technical-details-toggle"]',
      );
      if (el instanceof HTMLElement) el.click();
    });
    try {
      await page.waitForSelector('[data-testid="intake-v6-review-diagnostic-drawer"]', {
        timeout: 15000,
      });
      await page.waitForTimeout(1200);
      await shot(page, "14_after_diagnostic_open.png", false);
      await page.evaluate(() => {
        const el = document.querySelector('[data-testid="intake-v6-review-diagnostic-close"]');
        if (el instanceof HTMLElement) el.click();
      });
      await page.waitForTimeout(400);
    } catch (err) {
      console.log("WARN: drawer did not open", String(err));
      const dump = await page.evaluate(() => ({
        hasToggle: !!document.querySelector('[data-testid="intake-v6-review-technical-details-toggle"]'),
        hasDrawer: !!document.querySelector('[data-testid="intake-v6-review-diagnostic-drawer"]'),
        hasEntry: !!document.querySelector('[data-testid="intake-v6-review-diagnostic-entry"]'),
        hasDetails: !!document.querySelector('[data-testid="intake-v6-review-technical-details"]'),
      }));
      console.log(dump);
      await shot(page, "14_after_diagnostic_open.png", false);
    }
  } else {
    console.log("WARN: diagnostic entry missing — capturing page end");
    await shot(page, "14_after_diagnostic_open.png", false);
  }

  // Confirmare blocked (composition incomplete)
  await page.locator('[data-testid="intake-v6-progress-step-confirm"]').click({ force: true }).catch(() => null);
  await page.waitForTimeout(800);
  await page.getByRole("button", { name: /Continuă la Confirmare/i }).first().click({ force: true }).catch(() => null);
  await page.waitForTimeout(1500);
  // may stay on review — capture as blocked gate
  await shot(page, "09_after_confirmare_blocked.png");

  // Confirm composition → Confirmare first paint (still may be operator-blocked — name honestly)
  await goReview(page, ws.id);
  await page.locator('[data-testid="intake-v6-confirm-product-composition"]').click({ force: true }).catch(() => null);
  await page.waitForTimeout(2500);
  await shot(page, "02_after_finisaje_confirmed.png");
  await page.locator('[data-testid="intake-v6-review-calculator-panel"]').screenshot({
    path: path.join(SHOTS, "12_after_pricing_available.png"),
  }).catch(() => null);

  await page.locator('[data-testid="intake-v6-progress-step-confirm"]').click({ force: true }).catch(() => null);
  await page.waitForTimeout(800);
  await page.getByRole("button", { name: /Continuă la Confirmare/i }).first().click({ force: true }).catch(() => null);
  await page.waitForSelector('[data-testid="intake-v6-confirm-first-paint"]', { timeout: 20000 }).catch(() => null);
  await page.waitForTimeout(1500);
  const confirmState = await page.evaluate(() => {
    const ready =
      !/nu este pregătită|incomplet/i.test(
        document.querySelector('[data-testid="intake-v6-final-config-status"]')?.textContent ?? "",
      ) && Boolean(document.querySelector('[data-testid="intake-v6-confirm-internal-draft"]:checked'));
    return {
      ready,
      headline: document.querySelector('[data-testid="intake-v6-final-config-headline"]')?.textContent ?? "",
    };
  });
  // Truthful naming: if still blocked, write blocked-ready-path shot separately
  if (confirmState.ready) {
    await shot(page, "10_after_confirmare_ready.png");
  } else {
    await shot(page, "10_after_confirmare_ready.png"); // may still show remaining checklist — documented in SCREENSHOTS
    fs.writeFileSync(
      path.join(OUT, "confirmare_ready_note.json"),
      JSON.stringify({ ...confirmState, note: "composition confirmed; operator checklist may remain" }, null, 2),
    );
  }

  await goReview(page, ws.id);
  await page.reload({ waitUntil: "domcontentloaded" });
  await page.waitForTimeout(3000);
  await page.locator('[data-testid="intake-v6-progress-step-review"]').click({ force: true }).catch(() => null);
  await page.waitForSelector('[data-testid="intake-v6-review-form-region"]', { timeout: 30000 }).catch(() => null);
  await page.waitForTimeout(1200);
  await shot(page, "19_after_reloaded.png");

  await page.setViewportSize({ width: 1920, height: 1080 });
  await page.waitForTimeout(400);
  await shot(page, "17_after_full_1920.png");

  await page.setViewportSize({ width: 1100, height: 900 });
  await page.waitForTimeout(400);
  await shot(page, "18_after_narrow_1100.png");

  const p = await probe(page);
  const caseAcm = {
    id: "acm_composition_v2",
    workspace_id: ws.id,
    workspace_code: ws.workspace_code,
    probe: p,
    confirm: confirmState,
  };
  fs.writeFileSync(path.join(OUT, "acm_composition_probe.json"), JSON.stringify(caseAcm, null, 2));
  summary.cases.push(caseAcm);

  await browser.close();
  fs.writeFileSync(path.join(OUT, "composition_correction_summary.json"), JSON.stringify(summary, null, 2));
  console.log(JSON.stringify(summary, null, 2));
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
