/**
 * Desktop UI reset — evidence capture only. No product mutations beyond fixture setup.
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

fs.mkdirSync(OUT, { recursive: true });
fs.mkdirSync(SHOTS, { recursive: true });

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
  const face = page.locator('select[data-testid^="intake-v6-layer-role-"]').first();
  if ((await face.count()) > 0) {
    const opts = await face.locator("option").allTextContents();
    if (opts.some((t) => /fa[tț]ă|face/i.test(t))) await face.selectOption({ label: opts.find((t) => /fa[tț]ă|face/i.test(t)) }).catch(() => face.selectOption("face"));
    else await face.selectOption("face").catch(() => null);
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
  await page.locator('[data-testid="intake-v6-progress-step-review"]').click({ force: true }).catch(() => null);
  await page.waitForTimeout(2500);
}

async function shot(page, name, full = true) {
  await page.screenshot({ path: path.join(SHOTS, name), fullPage: full });
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const file = path.join(FIX, "litere-cu-fundal-acm-segmentat.svg");
  const ws = await createWs(`ui-reset-audit-${Date.now()}`);
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  const meta = { ui: UI, workspace_id: ws.id, at: new Date().toISOString(), shots: [] };

  await page.goto(`${UI}/intake-v6/${ws.id}/operator`, { waitUntil: "domcontentloaded", timeout: 120000 });
  await page.waitForTimeout(1500);
  await clientUpload(page, file);
  await shot(page, "01_page1_straturi_full.png");
  meta.shots.push("01_page1_straturi_full.png");

  // support role for ACM
  const support = page.locator('select[data-testid="intake-v6-layer-role-pseudo:fill-c5c6c6"]');
  if ((await support.count()) > 0) {
    await support.selectOption("support_panel");
    await page.waitForTimeout(3000);
  }
  await shot(page, "01b_page1_after_support_role.png");

  await confirmRoles(page);
  await goReview(page, ws.id);

  await shot(page, "02_finisaje_top.png");
  const letter = page.locator('[data-testid^="intake-v6-letter-group-"]').first();
  if ((await letter.count()) > 0) {
    await letter.click({ force: true }).catch(() => null);
    await page.waitForTimeout(600);
    await letter.screenshot({ path: path.join(SHOTS, "03_finisaje_letter_expanded.png") }).catch(() => null);
  }

  await page.getByRole("button", { name: /Iluminare/i }).first().click({ force: true }).catch(() => null);
  await page.waitForTimeout(1000);
  await shot(page, "04_iluminare_top.png");
  const results = page.locator('[data-testid="intake-v6-lighting-results"]');
  if ((await results.count()) > 0) await results.screenshot({ path: path.join(SHOTS, "05_iluminare_calculated_results.png") }).catch(() => null);
  else await shot(page, "05_iluminare_calculated_results.png");

  await page.getByRole("button", { name: /Montaj/i }).first().click({ force: true }).catch(() => null);
  await page.waitForTimeout(1200);
  await shot(page, "06_montaj_top.png");

  const commercial = page.locator('[data-testid="intake-v6-montaj-commercial-cluster"]');
  if ((await commercial.count()) > 0) {
    await commercial.locator("button").first().click({ force: true }).catch(() => null);
    await page.waitForTimeout(400);
    await commercial.screenshot({ path: path.join(SHOTS, "07_montaj_commercial.png") }).catch(() => null);
  }

  const fundal = page.locator('[data-testid="intake-v6-fundal-carcasa-cluster"]');
  if ((await fundal.count()) > 0) {
    await fundal.locator("button").first().click({ force: true }).catch(() => null);
    await page.waitForTimeout(500);
    await fundal.screenshot({ path: path.join(SHOTS, "08_fundal_carcasa.png") }).catch(() => null);
  }

  const supportPanel = page.locator('[data-testid="intake-v6-mounting-solution-panel"]');
  if ((await supportPanel.count()) > 0) await supportPanel.screenshot({ path: path.join(SHOTS, "09_support_structure.png") }).catch(() => null);

  const advanced = page.locator('[data-testid="intake-v6-montaj-advanced-cluster"]');
  if ((await advanced.count()) > 0) {
    await advanced.locator("button").first().click({ force: true }).catch(() => null);
    await page.waitForTimeout(400);
    await advanced.screenshot({ path: path.join(SHOTS, "10_montaj_avansat.png") }).catch(() => null);
  }

  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await page.waitForTimeout(400);
  await shot(page, "11_warnings_near_bottom.png", false);
  await shot(page, "12_montaj_full_scroll.png");

  const pricing = page.locator('[data-testid="intake-v6-review-calculator-panel"]');
  if ((await pricing.count()) > 0) await pricing.screenshot({ path: path.join(SHOTS, "13_pricing_rail.png") }).catch(() => null);

  await page.screenshot({ path: path.join(SHOTS, "14_footer.png"), clip: { x: 0, y: 820, width: 1440, height: 180 } }).catch(() => null);

  // Confirmare
  await page.locator('[data-testid="intake-v6-progress-step-confirm"]').click({ force: true }).catch(() => null);
  await page.waitForTimeout(1500);
  await page.getByRole("button", { name: /Continuă la Confirmare/i }).first().click({ force: true }).catch(() => null);
  await page.waitForTimeout(2000);
  await shot(page, "15_confirmare.png");
  const summaryToggle = page.locator('[data-testid="intake-v6-final-configuration-summary-toggle"]');
  if ((await summaryToggle.count()) > 0) {
    await summaryToggle.click({ force: true }).catch(() => null);
    await page.waitForTimeout(500);
    await shot(page, "15b_confirmare_expanded.png");
  }

  // drawer / footer issues on review
  await goReview(page, ws.id);
  const footerIssues = page.locator('[data-testid="intake-v6-footer-issues"] button, [data-testid="intake-v6-footer-issues-toggle"]').first();
  if ((await footerIssues.count()) > 0) {
    await footerIssues.click({ force: true }).catch(() => null);
    await page.waitForTimeout(400);
    await shot(page, "16_drawer_footer_issues.png", false);
  } else {
    await page.getByText(/blocante|avertizare|informaț/i).first().click({ force: true }).catch(() => null);
    await page.waitForTimeout(400);
    await shot(page, "16_drawer_footer_issues.png", false);
  }

  await page.setViewportSize({ width: 1100, height: 900 });
  await page.waitForTimeout(500);
  await shot(page, "17_narrow_desktop.png");

  // inventory probe
  const probe = await page.evaluate(() => {
    const text = document.body.innerText;
    const warnLike = Array.from(document.querySelectorAll("[class*='amber'],[class*='rose'],[class*='yellow']"))
      .slice(0, 40)
      .map((el) => (el.textContent || "").trim().slice(0, 120))
      .filter(Boolean);
    return {
      href: location.href,
      hasComposition: !!document.querySelector('[data-testid="intake-v6-product-composition-panel"]'),
      hasScope: !!document.querySelector('[data-testid="intake-v6-review-offer-scope-summary"]'),
      hasBlocker: !!document.querySelector('[data-testid="intake-v6-review-operator-blocker-banner"]'),
      hasPricing: !!document.querySelector('[data-testid="intake-v6-review-calculator-panel"]'),
      hasFooter: /Următorul pas/i.test(text),
      warnLikeSample: warnLike.slice(0, 15),
      viewport: { w: innerWidth, h: innerHeight },
    };
  });
  meta.probe = probe;
  fs.writeFileSync(path.join(OUT, "desktop_ui_reset_capture.json"), JSON.stringify(meta, null, 2));
  console.log(JSON.stringify(meta, null, 2));
  await browser.close();
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
