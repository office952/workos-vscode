/**
 * Letter pilot completion — live Page 2 screenshots on :3000 → :8003.
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
const FIX = "C:/Users/offic/Desktop/fisiere-teste-svg";
const BEFORE_SRC = path.join(
  __dirname,
  "../workos-configurator-letter-pilot-2026-07-19/screenshots",
);

fs.mkdirSync(OUT, { recursive: true });
fs.mkdirSync(SHOTS, { recursive: true });

function copyBeforeBaselines() {
  const map = [
    ["01_before_letter_config.png", "01_before_finisaje_full.png"],
    ["01_before_letter_config.png", "02_before_composition_scope.png"],
    ["01_before_letter_config.png", "03_before_pricing_rail.png"],
    ["02_before_lighting.png", "04_before_iluminare.png"],
    ["01_before_letter_config.png", "05_before_narrow_note.png"],
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

async function confirmAllRoles(page) {
  const confirmAll = page.getByRole("button", { name: /Confirmă toate|Confirmă rolurile|Acceptă propunerile/i }).first();
  if ((await confirmAll.count()) > 0) {
    await confirmAll.click({ force: true }).catch(() => null);
    await page.waitForTimeout(2500);
  } else {
    const selects = page.locator('select[data-testid^="intake-v6-layer-role-"]');
    const n = await selects.count();
    for (let i = 0; i < n; i++) {
      const sel = selects.nth(i);
      const val = await sel.inputValue().catch(() => null);
      if (!val) continue;
      await sel.selectOption(val).catch(() => null);
      await page.waitForTimeout(400);
    }
    await page.waitForTimeout(2000);
  }
  const next = page.getByRole("button", { name: /Continuă|Următor/i }).first();
  if ((await next.count()) > 0) await next.click({ force: true }).catch(() => null);
  await page.waitForTimeout(2000);
}

async function goReview(page, wsId) {
  await page.goto(`${UI}/intake-v6/${wsId}/operator`, { waitUntil: "domcontentloaded", timeout: 120000 });
  await page.waitForTimeout(1500);
  const review = page.locator('[data-testid="intake-v6-progress-step-review"]');
  if ((await review.count()) > 0) await review.click({ force: true }).catch(() => null);
  await page.waitForTimeout(2500);
}

async function probe(page) {
  return page.evaluate(() => {
    const text = document.body.innerText;
    return {
      href: location.href,
      composition: Boolean(document.querySelector('[data-testid="intake-v6-product-composition-panel"]')),
      compositionTitle: document.querySelector('[data-testid="intake-v6-product-composition-panel"]')?.textContent?.slice(0, 80),
      scope: Boolean(document.querySelector('[data-testid="intake-v6-review-offer-scope-summary"]')),
      pricing: Boolean(document.querySelector('[data-testid="intake-v6-review-calculator-panel"]')),
      pricingWeight: document
        .querySelector('[data-testid="intake-v6-review-calculator-panel"]')
        ?.getAttribute("data-pricing-weight"),
      commercialDisclosure: Boolean(
        document.querySelector('[data-testid="intake-v6-review-commercial-adjustments"]'),
      ),
      commercialExpanded: document
        .querySelector('[data-testid="intake-v6-review-commercial-adjustments"]')
        ?.getAttribute("data-expanded"),
      letterAnatomy: /Anatomie:\s*Față|Față · Cant · Spate|Față/i.test(text),
      lighting: Boolean(document.querySelector('[data-testid="intake-v6-review-tab-panels"]')),
      montaj: /Montaj|Fundal/i.test(text),
      rezultatComercial: /Rezultat comercial/i.test(text),
      technicalAuthorityOnL1: /authority live|TPL-BOND-CASETAT/i.test(
        document.querySelector('[data-testid="intake-v6-product-composition-panel"]')?.textContent ?? "",
      ),
      footerNext: /Următorul pas:/i.test(text),
    };
  });
}

async function main() {
  copyBeforeBaselines();
  const browser = await chromium.launch({ headless: true });
  const summary = { ui: UI, at: new Date().toISOString(), cases: [] };

  {
    const file = path.join(FIX, "litere-cu-fundal-acm-segmentat.svg");
    const ws = await createWs(`pilot-complete-acm-${Date.now()}`);
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
    await page.goto(`${UI}/intake-v6/${ws.id}/operator`, { waitUntil: "domcontentloaded", timeout: 120000 });
    await page.waitForTimeout(1500);
    await clientUpload(page, file);

    const support = page.locator('select[data-testid="intake-v6-layer-role-pseudo:fill-c5c6c6"]');
    if ((await support.count()) > 0) {
      await support.selectOption("support_panel");
      await page.waitForTimeout(3500);
    }
    const face = page.locator('select[data-testid="intake-v6-layer-role-pseudo:fill-e31e24"]');
    if ((await face.count()) > 0) {
      await face.selectOption("face");
      await page.waitForTimeout(1500);
    }
    await confirmAllRoles(page);
    await goReview(page, ws.id);
    await page.locator('[data-testid="intake-v6-progress-step-review"]').click({ force: true }).catch(() => null);
    await page.waitForTimeout(3000);

    await page.screenshot({ path: path.join(SHOTS, "06_finisaje_full.png"), fullPage: true });
    await page.locator('[data-testid="intake-v6-product-composition-panel"]').screenshot({
      path: path.join(SHOTS, "08_composition_compact.png"),
    }).catch(() => null);

    await page.locator('[data-testid="intake-v6-product-composition-toggle"]').click({ force: true }).catch(() => null);
    await page.waitForTimeout(300);
    // ensure details open
    const expanded = await page.locator('[data-testid="intake-v6-product-composition-toggle"]').getAttribute("aria-expanded");
    if (expanded !== "true") {
      await page.locator('[data-testid="intake-v6-product-composition-toggle"]').click({ force: true }).catch(() => null);
      await page.waitForTimeout(300);
    }
    await page.locator('[data-testid="intake-v6-product-composition-technical-toggle"]').click({ force: true }).catch(() => null);
    await page.waitForTimeout(400);
    await page.locator('[data-testid="intake-v6-product-composition-panel"]').screenshot({
      path: path.join(SHOTS, "09_composition_disclosure.png"),
    }).catch(() => null);

    await page.locator('[data-testid="intake-v6-review-offer-scope-summary"]').screenshot({
      path: path.join(SHOTS, "10_scope_blocker_state.png"),
    }).catch(() => null);
    // also capture blocker banner area
    await page.locator("body").screenshot({
      path: path.join(SHOTS, "10b_blocker_banner_area.png"),
      clip: { x: 280, y: 220, width: 780, height: 220 },
    }).catch(() => null);

    await page.locator('[data-testid="intake-v6-review-calculator-panel"]').screenshot({
      path: path.join(SHOTS, "11_pricing_compact.png"),
    }).catch(() => null);
    await page.locator('[data-testid="intake-v6-review-commercial-adjustments-toggle"]').click({ force: true }).catch(() => null);
    await page.waitForTimeout(400);
    await page.locator('[data-testid="intake-v6-live-calculation-sticky-shell"]').screenshot({
      path: path.join(SHOTS, "12_pricing_expanded.png"),
    }).catch(() => null);

    await page.getByRole("button", { name: /Iluminare/i }).first().click({ force: true }).catch(() => null);
    await page.waitForTimeout(1000);
    await page.screenshot({ path: path.join(SHOTS, "13_iluminare_results.png"), fullPage: true });

    await page.screenshot({
      path: path.join(SHOTS, "14_footer_sticky.png"),
      clip: { x: 0, y: 820, width: 1440, height: 180 },
    }).catch(() => null);

    await page.getByRole("button", { name: /Montaj/i }).first().click({ force: true }).catch(() => null);
    await page.waitForTimeout(1000);
    await page.screenshot({ path: path.join(SHOTS, "18_montaj_regression.png"), fullPage: true });

    await page.setViewportSize({ width: 390, height: 844 });
    await page.getByRole("button", { name: /Finisaje/i }).first().click({ force: true }).catch(() => null);
    await page.waitForTimeout(800);
    await page.screenshot({ path: path.join(SHOTS, "15_narrow_viewport.png"), fullPage: true });

    await page.setViewportSize({ width: 1440, height: 1000 });
    await page.reload({ waitUntil: "domcontentloaded" });
    await page.waitForTimeout(3000);
    await page.locator('[data-testid="intake-v6-progress-step-review"]').click({ force: true }).catch(() => null);
    await page.waitForTimeout(2000);
    await page.screenshot({ path: path.join(SHOTS, "16_reloaded.png"), fullPage: true });

    // Confirmare attempt (honest gate)
    await page.locator('[data-testid="intake-v6-progress-step-confirm"]').click({ force: true }).catch(() => null);
    await page.waitForTimeout(1500);
    await page.getByRole("button", { name: /Continuă la Confirmare/i }).first().click({ force: true }).catch(() => null);
    await page.waitForTimeout(1500);
    await page.screenshot({ path: path.join(SHOTS, "17_confirmare_regression.png"), fullPage: true });

    const p = await probe(page);
    const caseAcm = { id: "acm_page2", workspace_id: ws.id, probe: p };
    fs.writeFileSync(path.join(OUT, "acm_page2_probe.json"), JSON.stringify(caseAcm, null, 2));
    summary.cases.push(caseAcm);
    await page.close();
  }

  {
    const file = path.join(FIX, "litere-vol-1-layer.svg");
    const ws = await createWs(`pilot-complete-letters-${Date.now()}`);
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
    await page.goto(`${UI}/intake-v6/${ws.id}/operator`, { waitUntil: "domcontentloaded", timeout: 120000 });
    await clientUpload(page, file);
    const face = page.locator('select[data-testid^="intake-v6-layer-role-"]').first();
    if ((await face.count()) > 0) {
      await face.selectOption("face");
      await page.waitForTimeout(2000);
    }
    await confirmAllRoles(page);
    await goReview(page, ws.id);
    await page.locator('[data-testid="intake-v6-progress-step-review"]').click({ force: true }).catch(() => null);
    await page.waitForTimeout(2500);
    await page.screenshot({ path: path.join(SHOTS, "07_product_first_hierarchy.png"), fullPage: true });
    const p = await probe(page);
    summary.cases.push({ id: "simple_letters_page2", workspace_id: ws.id, probe: p });
    await page.close();
  }

  await browser.close();
  fs.writeFileSync(path.join(OUT, "pilot_completion_summary.json"), JSON.stringify(summary, null, 2));
  console.log(JSON.stringify(summary, null, 2));
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
