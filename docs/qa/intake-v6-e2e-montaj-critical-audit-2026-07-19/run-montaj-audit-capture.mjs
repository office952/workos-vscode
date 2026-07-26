/**
 * AUDIT-ONLY Montaj runtime capture — FE :3000 · BE via proxy · BACKEND_PORT=8003
 * No product mutations beyond navigation/tab clicks and optional expand.
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
fs.mkdirSync(OUT, { recursive: true });
fs.mkdirSync(SHOTS, { recursive: true });

const ACM_ID = process.env.ACM_WS ?? "3fb7a2b5-ec60-48e4-8b5c-c8649c0c8982";

async function shot(page, name) {
  const p = path.join(SHOTS, name);
  await page.screenshot({ path: p, fullPage: false });
  return p;
}

async function openOperator(page, id) {
  await page.goto(`${UI}/intake-v6/${id}/operator`, { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(1500);
}

async function clickTab(page, name) {
  const tab = page.getByRole("button", { name: new RegExp(name, "i") }).first();
  if (await tab.count()) await tab.click({ force: true });
  await page.waitForTimeout(600);
}

async function probe(page) {
  return page.evaluate(() => {
    const text = document.body?.innerText || "";
    return {
      url: location.href,
      hasFundal: /Fundal/i.test(text),
      hasScope: /Scope|pregătire|Pregătire|montaj la locație|Fără pregătire/i.test(text),
      hasTemplate: /șablon|sablon|Forex|Hârtie|Hartie/i.test(text),
      hasCable: /cablu|lungime cablu|mains/i.test(text),
      hasCorner: /colț|colt|service/i.test(text),
      hasSegmented: /panou|segment|îmbin|imbin/i.test(text),
      hasElectrical: /220|alimentare/i.test(text),
      hasProductSystem: /Product System/i.test(text),
      hasTarifeLipsa: /Tarife lips/i.test(text),
      hasAccesorii: /Accesorii montaj/i.test(text),
      attention: document.querySelector("[data-attention-weight]")?.textContent?.trim() || null,
      formLeads: !!document.querySelector("[data-form-leads]"),
    };
  });
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  const page = await context.newPage();
  const summary = { ui: UI, acm: ACM_ID, shots: [], probes: {} };

  // ACM workspace — Montaj first paint
  await openOperator(page, ACM_ID);
  await clickTab(page, "Montaj");
  summary.probes.acm_montaj = await probe(page);
  summary.shots.push(await shot(page, "01_montaj_acm_first_paint_1440.png"));

  // Expand commercial if present
  const commercial = page.getByText(/pregătire|Scope ofert|Scope montaj|Montaj comercial|pregătire pentru montaj/i).first();
  if (await commercial.count()) {
    await commercial.click({ force: true }).catch(() => {});
    await page.waitForTimeout(400);
  }
  summary.probes.acm_commercial = await probe(page);
  summary.shots.push(await shot(page, "02_montaj_acm_commercial_region.png"));

  // Pricing rail visible
  summary.shots.push(await shot(page, "03_montaj_acm_pricing_viewport.png"));

  // Confirmare
  const confirmTab = page.getByRole("button", { name: /Confirmare|Continuă|Confirm/i }).first();
  // Prefer in-app Confirmare nav if present
  const confLink = page.locator('a[href*="confirm"], button:has-text("Confirmare")').first();
  if (await confLink.count()) {
    await confLink.click({ force: true });
    await page.waitForTimeout(1200);
  } else {
    await page.goto(`${UI}/intake-v6/${ACM_ID}/confirm`, { waitUntil: "networkidle" }).catch(() => {});
    await page.waitForTimeout(1200);
  }
  summary.probes.confirmare = await probe(page);
  summary.shots.push(await shot(page, "04_confirmare_acm.png"));

  // Diagnostic drawer
  await openOperator(page, ACM_ID);
  await clickTab(page, "Montaj");
  const diag = page.getByRole("button", { name: /diagnostic/i }).first();
  if (await diag.count()) {
    summary.shots.push(await shot(page, "05_diagnostic_closed.png"));
    await diag.click({ force: true });
    await page.waitForTimeout(800);
    summary.shots.push(await shot(page, "06_diagnostic_open.png"));
  }

  // Reload persistence visual
  await page.reload({ waitUntil: "networkidle" });
  await clickTab(page, "Montaj");
  summary.probes.after_reload = await probe(page);
  summary.shots.push(await shot(page, "07_montaj_acm_after_reload.png"));

  // Viewports
  await page.setViewportSize({ width: 1920, height: 1080 });
  await page.waitForTimeout(300);
  summary.shots.push(await shot(page, "08_montaj_acm_1920.png"));
  await page.setViewportSize({ width: 1100, height: 900 });
  await page.waitForTimeout(300);
  summary.shots.push(await shot(page, "09_montaj_acm_1100.png"));
  await page.setViewportSize({ width: 1440, height: 1000 });

  // API refresh after UI
  const ws = await (await fetch(`${API}/workspaces/${ACM_ID}`)).json();
  const fsSetup = ws.payload?.finish_setup || {};
  summary.api = {
    mounting_scope: fsSetup.mounting_scope,
    mounting_template_enabled: fsSetup.mounting_template_enabled,
    mounting_solution: fsSetup.mounting_solution?.template_code || null,
    segmented: fsSetup.segmented_background?.status || null,
    cable: fsSetup.mains_cable_length_m ?? null,
    corner: fsSetup.power_supply_service_corner ?? null,
    confirmed: fsSetup.confirmed,
  };

  // Try list recent simple-letter workspace (no support) from list endpoint — lightweight titles only via existing ACM contrast
  summary.notes = [
    "Acceptance UI is :3000 (not :3001).",
    "ACM workspace already has product_system ACM mounting_solution with commercial mounting_scope=none and template_enabled=true — contradiction candidate.",
  ];

  fs.writeFileSync(path.join(OUT, "montaj_capture_summary.json"), JSON.stringify(summary, null, 2));
  console.log(JSON.stringify(summary, null, 2));
  await browser.close();
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
