/**
 * Live Page-2 IA verification + screenshots (docs-only runner).
 * Usage:
 *   $env:PW_BACKEND_URL='http://127.0.0.1:8003'
 *   $env:PW_BASE_URL='http://127.0.0.1:3001'
 *   node docs/qa/intake-v6-page2-ia-montaj-realignment-2026-07-19/run-page2-ia-live.mjs
 */
import { chromium } from "../../../frontend/node_modules/playwright/index.mjs";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const BACKEND = process.env.PW_BACKEND_URL ?? "http://127.0.0.1:8003";
const UI = process.env.PW_BASE_URL ?? "http://127.0.0.1:3001";
const DESKTOP = path.join(process.env.USERPROFILE || "", "Desktop", "fisiere-teste-svg");
const OUT = path.join(__dirname, "screenshots");
const LOG = path.join(__dirname, "runtime");
const SVG = path.join(DESKTOP, "litere-cu-fundal-acm-segmentat.svg");
const SVG_CROSS = path.join(DESKTOP, "litere-cu-fundal-acm-segmentat-litera-peste-imbinare.svg");

fs.mkdirSync(OUT, { recursive: true });
fs.mkdirSync(LOG, { recursive: true });

function writeJson(name, data) {
  fs.writeFileSync(path.join(LOG, name), JSON.stringify(data, null, 2), "utf8");
}
async function api(pathname, init) {
  const res = await fetch(`${BACKEND}${pathname}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    signal: AbortSignal.timeout(30_000),
  });
  const body = await res.json().catch(() => null);
  return { status: res.status, body };
}
async function createWorkspace(title) {
  const r = await api("/api/v1/intake-v6/workspaces", {
    method: "POST",
    body: JSON.stringify({ title, analyzer_mode: "analyzer_first" }),
  });
  if (r.status >= 400) throw new Error(`create ${r.status}`);
  return r.body;
}
async function getWorkspace(id) {
  return (await api(`/api/v1/intake-v6/workspaces/${id}`)).body;
}
async function waitAuth(page) {
  await page.getByText("Se verifică sesiunea").waitFor({ state: "detached", timeout: 60_000 }).catch(() => {});
}
async function gotoOperator(page, id) {
  await page.goto(`${UI}/intake-v6/${id}/operator`, { waitUntil: "domcontentloaded", timeout: 120_000 });
  await waitAuth(page);
  await page.getByTestId("intake-v6-header").waitFor({ state: "visible", timeout: 90_000 });
}
async function importSvg(page, svgPath) {
  const input = page.getByTestId("intake-v6-svg-input");
  await input.waitFor({ state: "attached", timeout: 60_000 });
  await input.setInputFiles(svgPath);
  const started = Date.now();
  while (Date.now() - started < 90_000) {
    if (await page.getByTestId("intake-v6-file-confirm-chip").isVisible().catch(() => false)) return;
    if (await page.getByText(/Fișier recunoscut|Fisier recunoscut/i).isVisible().catch(() => false)) return;
    if ((await page.locator('[data-testid^="intake-v6-layer-role-"]').count().catch(() => 0)) > 0) return;
    if (await page.getByText(/Decizii straturi/i).isVisible().catch(() => false)) return;
    await page.waitForTimeout(500);
  }
  throw new Error("SVG import did not surface analyzer UI");
}
async function assignConturSuport(page) {
  const roleSelects = page.locator('[data-testid^="intake-v6-layer-role-"]');
  await roleSelects.first().waitFor({ state: "attached", timeout: 60_000 }).catch(() => {});
  const count = await roleSelects.count();
  for (let i = 0; i < count; i += 1) {
    const sel = roleSelects.nth(i);
    const testId = (await sel.getAttribute("data-testid")) || "";
    const html = await sel.innerHTML().catch(() => "");
    if (!/support_panel|Contur suport/i.test(html)) continue;
    if (/gravare|fundal|acm|cnc-135/i.test(testId) || !/letter|decupare|outside/i.test(testId)) {
      await sel.selectOption("support_panel").catch(async () => {
        const opts = await sel.locator("option").allTextContents();
        const label = opts.find((o) => /contur suport/i.test(o));
        if (label) await sel.selectOption({ label });
      });
      await page.waitForTimeout(2500);
      return true;
    }
  }
  return false;
}
async function advanceToReview(page) {
  const confirmAll = page.getByTestId("intake-v6-confirm-all-roles");
  if (await confirmAll.isVisible().catch(() => false)) {
    await confirmAll.click();
    await page.waitForTimeout(1500);
  }
  if (!(await page.getByTestId("intake-v6-step-review").isVisible().catch(() => false))) {
    await page.getByTestId("intake-v6-footer-next").click({ timeout: 90_000 });
  }
  await page.getByTestId("intake-v6-step-review").waitFor({ state: "visible", timeout: 90_000 });
}

async function main() {
  const compat = await api("/api/v1/system/local-compatibility");
  writeJson("compat.json", compat);
  if (compat.status !== 200) throw new Error("compat fail");

  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const findings = [];

  const ws = await createWorkspace("page2-ia-live");
  writeJson("workspace.json", ws);
  await gotoOperator(page, ws.id);
  await importSvg(page, SVG);
  await page.waitForTimeout(2500);
  await assignConturSuport(page);
  await page.waitForTimeout(2000);
  await advanceToReview(page);

  await page.screenshot({ path: path.join(OUT, "01_page2_top.png"), fullPage: false });
  const sticky = await page.getByTestId("intake-v6-review-operator-blocker-banner").getAttribute("data-sticky");
  findings.push({ stickyBanner: sticky });

  // Tab labels
  const iluminareTab = page.getByTestId("intake-v6-review-tab-iluminare");
  const iluminareText = ((await iluminareTab.textContent()) || "").trim();
  findings.push({ iluminareTab: iluminareText });
  if (!/Iluminare și surse|Iluminare si surse/i.test(iluminareText)) {
    findings.push({ error: "Iluminare tab label missing rename" });
  }

  await page.getByTestId("intake-v6-review-tab-finisaje").click();
  await page.screenshot({ path: path.join(OUT, "02_finisaje.png"), fullPage: true });

  await iluminareTab.click();
  await page.waitForTimeout(500);
  await page.screenshot({ path: path.join(OUT, "03_iluminare_si_surse.png"), fullPage: true });
  const psuSub = await page.getByTestId("intake-v6-electrical-subsection").isVisible().catch(() => false);
  const psuTitle = await page.getByTestId("intake-v6-electrical-subsection").textContent().catch(() => "");
  findings.push({ psuSub, psuTitle: (psuTitle || "").slice(0, 120) });

  await page.getByTestId("intake-v6-review-tab-montaj").click();
  await page.waitForTimeout(800);
  await page.screenshot({ path: path.join(OUT, "04_montaj_top.png"), fullPage: false });

  const fundal = page.getByTestId("intake-v6-fundal-carcasa-cluster");
  await fundal.scrollIntoViewIfNeeded().catch(() => {});
  const fundalVisible = await fundal.isVisible().catch(() => false);
  findings.push({ fundalVisible });
  await page.screenshot({ path: path.join(OUT, "05_fundal_carcasa.png"), fullPage: false });

  const seg = page.getByTestId("intake-v6-segmented-background-panel");
  await seg.scrollIntoViewIfNeeded().catch(() => {});
  await page.screenshot({ path: path.join(OUT, "06_segmented_proposal.png"), fullPage: false });
  if (await page.getByTestId("intake-v6-segmented-confirm").isEnabled().catch(() => false)) {
    await page.getByTestId("intake-v6-segmented-confirm").click();
    await page.waitForTimeout(2000);
  }
  await page.screenshot({ path: path.join(OUT, "07_segmented_confirmed.png"), fullPage: false });

  const elec = page.getByTestId("intake-v6-segmented-electrical-panel");
  const elecVisible = await elec.isVisible().catch(() => false);
  findings.push({ elecVisible });
  if (elecVisible) {
    await elec.scrollIntoViewIfNeeded();
    await page.screenshot({ path: path.join(OUT, "08_per_panel_220v.png"), fullPage: false });
    const supplies = page.locator('[data-testid^="intake-v6-elec-supply-"]');
    const n = await supplies.count();
    if (n >= 2) {
      const ids = await page.evaluate(() =>
        [...document.querySelectorAll('[data-testid^="intake-v6-elec-supply-"]')].map((el) =>
          (el.getAttribute("data-testid") || "").replace("intake-v6-elec-supply-", ""),
        ),
      );
      await page.getByTestId(`intake-v6-elec-supply-${ids[0]}`).selectOption("DIRECT_220V").catch(() => {});
      await page.getByTestId(`intake-v6-elec-position-${ids[0]}`).selectOption("BOTTOM_LEFT").catch(() => {});
      await page.getByTestId(`intake-v6-elec-supply-${ids[1]}`).selectOption("SHARED_FROM_PANEL").catch(() => {});
      await page.getByTestId(`intake-v6-elec-shared-${ids[1]}`).selectOption(ids[0]).catch(() => {});
      await page.waitForTimeout(800);
      await page.screenshot({ path: path.join(OUT, "09_shared_supply.png"), fullPage: false });
      const confirmElec = page.getByTestId("intake-v6-segmented-electrical-confirm");
      if (await confirmElec.isEnabled().catch(() => false)) {
        await confirmElec.click();
        await page.waitForTimeout(1200);
      }
    }
  }

  // Legacy corner should be superseded when segmented confirmed
  const legacyInput = await page.getByTestId("intake-v6-power-supply-service-corner").isVisible().catch(() => false);
  const superseded = await page.getByTestId("intake-v6-legacy-corner-superseded-note").isVisible().catch(() => false);
  findings.push({ legacyInputVisible: legacyInput, supersededNote: superseded });

  const commercial = page.getByTestId("intake-v6-montaj-commercial-cluster");
  findings.push({
    commercialExpanded: await commercial.getAttribute("data-expanded"),
  });
  const advanced = page.getByTestId("intake-v6-montaj-advanced-cluster");
  findings.push({ advancedExpanded: await advanced.getAttribute("data-expanded") });

  await page.screenshot({ path: path.join(OUT, "10_sticky_blocker.png"), fullPage: false });
  await page.screenshot({ path: path.join(OUT, "11_montaj_full.png"), fullPage: true });

  // Tab still navigable while blocked
  await page.getByTestId("intake-v6-review-tab-finisaje").click();
  await page.waitForTimeout(300);
  await page.getByTestId("intake-v6-review-tab-montaj").click();
  findings.push({ tabNavWhileBlocked: true });

  await page.reload({ waitUntil: "domcontentloaded" });
  await waitAuth(page);
  await page.getByTestId("intake-v6-review-tab-montaj").click().catch(() => {});
  await page.waitForTimeout(1200);
  await page.screenshot({ path: path.join(OUT, "12_reload.png"), fullPage: true });
  const after = await getWorkspace(ws.id);
  writeJson("workspace_after_reload.json", {
    seg: after?.payload?.finish_setup?.segmented_background?.status,
    elec: after?.payload?.finish_setup?.segmented_background?.electrical_connection_management?.status,
  });

  // Cross SVG smoke (best-effort)
  try {
    const ws2 = await createWorkspace("page2-ia-cross");
    await gotoOperator(page, ws2.id);
    await importSvg(page, SVG_CROSS);
    await page.waitForTimeout(2000);
    await assignConturSuport(page);
    await advanceToReview(page);
    await page.getByTestId("intake-v6-review-tab-montaj").click();
    await page.waitForTimeout(1000);
    await page.screenshot({ path: path.join(OUT, "13_cross_montaj.png"), fullPage: true });
    findings.push({ crossOk: true });
  } catch (err) {
    findings.push({ crossOk: false, crossError: String(err) });
  }

  writeJson("findings.json", findings);
  await browser.close();
  console.log(JSON.stringify(findings, null, 2));
}

main().catch((err) => {
  console.error(err);
  writeJson("fatal.json", { message: String(err), stack: err?.stack });
  process.exit(1);
});
