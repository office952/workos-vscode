/**
 * Docs-only LIVE Intake V6 complete operator walkthrough (read-only product code).
 * Captures screenshots + runtime JSON for the canonical UI/UX audit.
 *
 * Usage (from repo root):
 *   $env:PW_BACKEND_URL='http://127.0.0.1:8003'
 *   $env:PW_BASE_URL='http://127.0.0.1:3001'
 *   node docs/qa/intake-v6-complete-ui-ux-audit-2026-07-19/run-complete-audit.mjs
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
const SVG_BASIC = path.join(DESKTOP, "litere-cu-fundal-acm-segmentat.svg");
const SVG_CROSS = path.join(DESKTOP, "litere-cu-fundal-acm-segmentat-litera-peste-imbinare.svg");
const SVG_SIT3 = path.join(DESKTOP, "situatie-3.svg");

fs.mkdirSync(OUT, { recursive: true });
fs.mkdirSync(LOG, { recursive: true });

const findings = [];
function note(sev, msg, extra = {}) {
  findings.push({ sev, msg, ...extra, at: new Date().toISOString() });
  console.log(`[${sev}] ${msg}`);
}
function writeJson(name, data) {
  fs.writeFileSync(path.join(LOG, name), JSON.stringify(data, null, 2), "utf8");
}
async function shot(page, name, opts = {}) {
  const p = path.join(OUT, name);
  await page.screenshot({ path: p, fullPage: Boolean(opts.fullPage), ...opts });
  return p;
}
async function api(pathname, init) {
  const res = await fetch(`${BACKEND}${pathname}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    signal: AbortSignal.timeout(30_000),
  });
  const text = await res.text();
  let body = null;
  try {
    body = JSON.parse(text);
  } catch {
    body = text;
  }
  return { status: res.status, body };
}
async function createWorkspace(title) {
  const r = await api("/api/v1/intake-v6/workspaces", {
    method: "POST",
    body: JSON.stringify({ title, analyzer_mode: "analyzer_first" }),
  });
  if (r.status >= 400) throw new Error(`create workspace ${r.status}`);
  return r.body;
}
async function getWorkspace(id) {
  return (await api(`/api/v1/intake-v6/workspaces/${id}`)).body;
}
async function getPd(id) {
  return api(
    `/api/v1/product-system/product-definition/${encodeURIComponent("TPL-VOLUMETRIC-LETTERS_v2")}?workspace_id=${encodeURIComponent(id)}`,
  );
}
async function getAgg(id) {
  return api(
    `/api/v1/product-system/aggregate/${encodeURIComponent("TPL-VOLUMETRIC-LETTERS_v2")}?workspace_id=${encodeURIComponent(id)}`,
  );
}
async function putFinish(id, finish) {
  return api(`/api/v1/intake-v6/workspaces/${id}/finish-setup`, {
    method: "PUT",
    body: JSON.stringify(finish),
  });
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
  await page.getByTestId("intake-v6-file-confirm-chip").waitFor({ state: "visible", timeout: 90_000 });
}
async function assignConturSuport(page) {
  const roleSelects = page.locator('[data-testid^="intake-v6-layer-role-"]');
  await roleSelects.first().waitFor({ state: "attached", timeout: 60_000 }).catch(() => {});
  const count = await roleSelects.count();
  const ranked = [];
  for (let i = 0; i < count; i += 1) {
    const sel = roleSelects.nth(i);
    const testId = (await sel.getAttribute("data-testid")) || "";
    const html = await sel.innerHTML().catch(() => "");
    if (!/support_panel|Contur suport/i.test(html)) continue;
    let score = 0;
    if (/gravare|fundal|acm|alucobond|support|panel|cnc-135/i.test(testId)) score += 10;
    if (/letter|litere|logo|decupare|outside/i.test(testId)) score -= 5;
    ranked.push({ i, score });
  }
  ranked.sort((a, b) => b.score - a.score);
  for (const { i } of ranked) {
    const sel = roleSelects.nth(i);
    await sel.selectOption("support_panel").catch(async () => {
      const opts = await sel.locator("option").allTextContents();
      const label = opts.find((o) => /contur suport/i.test(o));
      if (label) await sel.selectOption({ label });
    });
    await page.waitForTimeout(2500);
    const err = page.getByText(/Nu s-a putut asocia|necesită candidați closed-contour/i);
    if (await err.isVisible().catch(() => false)) continue;
    return true;
  }
  return ranked.length > 0;
}
async function waitSeg(id, statuses, timeoutMs = 45_000) {
  const want = new Set(statuses.map((s) => s.toUpperCase()));
  const started = Date.now();
  let last = null;
  while (Date.now() - started < timeoutMs) {
    const snap = await getWorkspace(id);
    last = snap?.payload?.finish_setup?.segmented_background || null;
    if (want.has(String(last?.status || "").toUpperCase())) return last;
    await new Promise((r) => setTimeout(r, 800));
  }
  return last;
}
async function waitAnalysis(id, timeoutMs = 60_000) {
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    const snap = await getWorkspace(id);
    if (snap?.payload?.svg_analysis_json && snap?.payload?.layer_role_setup) return snap;
    await new Promise((r) => setTimeout(r, 800));
  }
  return null;
}
async function goReviewTab(page, tabId) {
  const tab = page.getByTestId(`intake-v6-review-tab-${tabId}`);
  if (await tab.count()) await tab.click();
  else await page.getByRole("tab", { name: new RegExp(tabId, "i") }).click().catch(() => {});
  await page.waitForTimeout(600);
  const panel = page.getByTestId(`intake-v6-review-tab-panel-${tabId}`);
  const visible = await panel.isVisible().catch(() => false);
  return visible;
}
async function advanceToReview(page) {
  const confirmAll = page.getByTestId("intake-v6-confirm-all-roles");
  if (await confirmAll.isVisible().catch(() => false)) {
    await confirmAll.click();
    await page.waitForTimeout(1500);
  }
  if (await confirmAll.isVisible().catch(() => false)) {
    await confirmAll.click();
    await page.waitForTimeout(1000);
  }
  const already = await page.getByTestId("intake-v6-step-review").isVisible().catch(() => false);
  if (!already) {
    const footer = page.getByTestId("intake-v6-footer-next");
    await footer.waitFor({ state: "visible", timeout: 90_000 });
    await footer.click({ timeout: 90_000 }).catch(() => {});
  }
  await page.getByTestId("intake-v6-step-review").waitFor({ state: "visible", timeout: 90_000 });
}
async function scrollCapture(page, prefix) {
  await shot(page, `${prefix}_top.png`, { fullPage: false });
  await page.evaluate(() => window.scrollTo(0, Math.floor(document.body.scrollHeight * 0.45)));
  await page.waitForTimeout(200);
  await shot(page, `${prefix}_mid.png`, { fullPage: false });
  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await page.waitForTimeout(200);
  await shot(page, `${prefix}_bottom.png`, { fullPage: false });
  await shot(page, `${prefix}_full.png`, { fullPage: true });
  const metrics = await page.evaluate(() => ({
    scrollHeight: document.body.scrollHeight,
    clientHeight: window.innerHeight,
    scrollDepth: document.body.scrollHeight / Math.max(window.innerHeight, 1),
  }));
  return metrics;
}
async function collectUiInventory(page) {
  return page.evaluate(() => {
    const text = (el) => (el?.textContent || "").replace(/\s+/g, " ").trim().slice(0, 160);
    const cards = [...document.querySelectorAll("[class*='rounded'][class*='border']")].slice(0, 80).map((el, i) => ({
      i,
      testid: el.getAttribute("data-testid"),
      text: text(el).slice(0, 100),
      h: el.getBoundingClientRect().height,
    }));
    const badges = [...document.querySelectorAll("[class*='badge'], [class*='pill'], span")]
      .filter((el) => /badge|pill|Confirmat|Blocat|Necesită|PROPOSED|DRAFT|warning|blocker/i.test(el.className + el.textContent))
      .slice(0, 40)
      .map((el) => text(el));
    const tabs = [...document.querySelectorAll('[data-testid^="intake-v6-review-tab-"]')]
      .filter((el) => !el.getAttribute("data-testid")?.includes("panel"))
      .map((el) => ({ id: el.getAttribute("data-testid"), text: text(el), selected: el.getAttribute("aria-selected") }));
    const blockers = [...document.querySelectorAll('[data-testid*="blocker"], [class*="rose"], [class*="amber"]')]
      .slice(0, 30)
      .map((el) => ({ testid: el.getAttribute("data-testid"), text: text(el).slice(0, 120) }));
    return {
      url: location.href,
      title: document.title,
      tabs,
      cardCountApprox: cards.length,
      tallCards: cards.filter((c) => c.h > 280).slice(0, 20),
      badges: badges.slice(0, 25),
      blockers: blockers.slice(0, 20),
      headings: [...document.querySelectorAll("h1,h2,h3")].slice(0, 30).map((el) => text(el)),
    };
  });
}

async function runPrimaryFlow(browser) {
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const apiHits = [];
  page.on("response", (res) => {
    const u = res.url();
    if (u.includes("/api/")) {
      apiHits.push({ url: u.replace(BACKEND, "").replace(UI, ""), status: res.status(), method: res.request().method() });
    }
  });

  // Preflight pages
  await page.goto(UI + "/", { waitUntil: "domcontentloaded", timeout: 60_000 });
  await shot(page, "00_app_root.png");

  const compat = await api("/api/v1/system/local-compatibility");
  writeJson("compat.json", compat);
  if (compat.status !== 200) note("CRITICAL", "Compatibility endpoint failed on audit backend", compat);

  const ws = await createWorkspace("audit-complete-ui-ux-basic");
  writeJson("workspace_basic.json", ws);
  note("INFO", `Created workspace ${ws.id} / ${ws.workspace_code}`);

  await gotoOperator(page, ws.id);
  await shot(page, "01_pas1_empty.png", { fullPage: true });
  const emptyInv = await collectUiInventory(page);
  writeJson("inv_01_empty.json", emptyInv);

  await importSvg(page, SVG_BASIC);
  await shot(page, "02_pas1_imported.png", { fullPage: true });
  await page.waitForTimeout(2000);
  const analysis = await waitAnalysis(ws.id);
  writeJson("analysis_basic.json", {
    ok: Boolean(analysis),
    readiness: analysis?.readiness_status,
    layers: analysis?.payload?.layer_role_setup,
  });

  await shot(page, "03_pas1_layers_mid.png", { fullPage: true });
  const m1 = await scrollCapture(page, "04_pas1");
  writeJson("metrics_pas1.json", m1);

  await assignConturSuport(page);
  await page.waitForTimeout(2500);
  let proposal = await waitSeg(ws.id, ["PROPOSED", "CONFIRMED"], 35_000);
  writeJson("proposal_after_contur.json", proposal);
  await shot(page, "05_pas1_after_contur_suport.png", { fullPage: true });

  await advanceToReview(page);
  await shot(page, "06_pas2_entry_finisaje.png", { fullPage: true });
  const finMetrics = await scrollCapture(page, "07_finisaje");
  writeJson("metrics_finisaje.json", finMetrics);
  writeJson("inv_finisaje.json", await collectUiInventory(page));

  await goReviewTab(page, "iluminare");
  await shot(page, "08_iluminare_full.png", { fullPage: true });
  const ilumMetrics = await scrollCapture(page, "09_iluminare");
  writeJson("metrics_iluminare.json", ilumMetrics);
  writeJson("inv_iluminare.json", await collectUiInventory(page));
  const elecSub = await page.getByTestId("intake-v6-electrical-subsection").isVisible().catch(() => false);
  note(elecSub ? "INFO" : "WARN", `Iluminare Electrică/PSU subsection visible=${elecSub}`);

  await goReviewTab(page, "montaj");
  await shot(page, "10_montaj_top.png", { fullPage: false });
  const montajMetrics = await scrollCapture(page, "11_montaj");
  writeJson("metrics_montaj.json", montajMetrics);
  writeJson("inv_montaj.json", await collectUiInventory(page));

  const segPanel = page.getByTestId("intake-v6-segmented-background-panel");
  const segVisible = await segPanel.isVisible().catch(() => false);
  note(segVisible ? "INFO" : "HIGH", `Segmented panel visible on Montaj=${segVisible}`);
  if (!segVisible) {
    proposal = await waitSeg(ws.id, ["PROPOSED", "CONFIRMED"], 15_000);
    writeJson("proposal_retry.json", proposal);
  }

  if (segVisible || (await segPanel.isVisible().catch(() => false))) {
    await segPanel.scrollIntoViewIfNeeded().catch(() => {});
    await shot(page, "12_segmented_proposal.png", { fullPage: false });
    const status = await page.getByTestId("intake-v6-segmented-status").textContent().catch(() => "");
    const confirmEnabled = await page.getByTestId("intake-v6-segmented-confirm").isEnabled().catch(() => false);
    note("INFO", `Segmented status="${status}" confirmEnabled=${confirmEnabled}`);

    if (confirmEnabled) {
      await page.getByTestId("intake-v6-segmented-confirm").click();
      await page.waitForTimeout(2000);
      await shot(page, "13_segmented_confirmed.png", { fullPage: false });
      const confirmed = await waitSeg(ws.id, ["CONFIRMED"], 30_000);
      writeJson("finish_confirmed.json", confirmed);
    }
  } else {
    note("HIGH", "Could not confirm segmented — panel missing");
  }

  // Electrical after confirm
  const elecPanel = page.getByTestId("intake-v6-segmented-electrical-panel");
  let elecVisible = await elecPanel.isVisible().catch(() => false);
  if (!elecVisible) {
    await page.waitForTimeout(1500);
    elecVisible = await elecPanel.isVisible().catch(() => false);
  }
  note(elecVisible ? "INFO" : "HIGH", `Segmented electrical panel visible=${elecVisible}`);
  if (elecVisible) {
    await elecPanel.scrollIntoViewIfNeeded();
    await shot(page, "14_electrical_draft.png", { fullPage: false });
    // Configure shared feed if controls exist
    const modeSelects = page.locator('[data-testid^="intake-v6-elec-supply-"]');
    const n = await modeSelects.count();
    writeJson("electrical_controls.json", { modeSelectCount: n });
    if (n >= 2) {
      const panelIds = await page.evaluate(() =>
        [...document.querySelectorAll('[data-testid^="intake-v6-elec-supply-"]')].map((el) =>
          (el.getAttribute("data-testid") || "").replace("intake-v6-elec-supply-", ""),
        ),
      );
      const a = panelIds[0];
      const b = panelIds[1];
      await page.getByTestId(`intake-v6-elec-supply-${a}`).selectOption("DIRECT_220V").catch(() => {});
      await page.getByTestId(`intake-v6-elec-position-${a}`).selectOption("BOTTOM_LEFT").catch(() => {});
      await page.getByTestId(`intake-v6-elec-supply-${b}`).selectOption("SHARED_FROM_PANEL").catch(() => {});
      await page.getByTestId(`intake-v6-elec-shared-${b}`).selectOption(a).catch(() => {});
      await page.waitForTimeout(1000);
      await shot(page, "15_electrical_shared_configured.png", { fullPage: false });
      const confirmElec = page.getByTestId("intake-v6-segmented-electrical-confirm");
      if (await confirmElec.isVisible().catch(() => false)) {
        const en = await confirmElec.isEnabled().catch(() => false);
        note("INFO", `Electrical confirm enabled=${en}`);
        if (en) {
          await confirmElec.click();
          await page.waitForTimeout(1500);
          await shot(page, "16_electrical_confirmed.png", { fullPage: false });
        } else {
          await shot(page, "16_electrical_confirm_disabled.png", { fullPage: false });
          const blockers = await page.getByTestId("intake-v6-elec-blockers").textContent().catch(() => "");
          note("WARN", `Electrical confirm blocked: ${blockers}`);
        }
      }
    }
  }

  // Legacy service corner coexistence
  const serviceCorner = await page.getByTestId("intake-v6-power-supply-service-corner").isVisible().catch(() => false);
  const acpCorner = await page.getByTestId("intake-v6-acp-service-corner-fields").isVisible().catch(() => false);
  note("INFO", `Legacy service corner visible=${serviceCorner} acpCorner=${acpCorner}`);
  await shot(page, "17_montaj_service_corner_region.png", { fullPage: true });

  // Reload persistence
  await page.reload({ waitUntil: "domcontentloaded" });
  await waitAuth(page);
  await page.getByTestId("intake-v6-step-review").waitFor({ state: "visible", timeout: 90_000 }).catch(async () => {
    await page.getByTestId("intake-v6-progress-step-review").click().catch(() => {});
  });
  await goReviewTab(page, "montaj");
  await page.waitForTimeout(1500);
  await shot(page, "18_reload_montaj.png", { fullPage: true });
  const afterReload = await getWorkspace(ws.id);
  writeJson("workspace_after_reload.json", {
    seg: afterReload?.payload?.finish_setup?.segmented_background,
    service_corner: afterReload?.payload?.finish_setup?.power_supply_service_corner,
  });

  // Confirm step
  const footer = page.getByTestId("intake-v6-footer-next");
  const flabel = ((await footer.textContent().catch(() => "")) || "").trim();
  if (/Confirmare/i.test(flabel) && (await footer.isEnabled().catch(() => false))) {
    await footer.click();
    await page.waitForTimeout(1500);
    await shot(page, "19_pas3_confirmare.png", { fullPage: true });
    writeJson("inv_confirmare.json", await collectUiInventory(page));
  } else {
    note("WARN", `Could not advance to Confirmare; footer="${flabel}" enabled=${await footer.isEnabled().catch(() => false)}`);
    await shot(page, "19_pas3_not_reached.png", { fullPage: true });
  }

  const pd = await getPd(ws.id);
  const agg = await getAgg(ws.id);
  writeJson("pd_basic.json", pd);
  writeJson("agg_basic.json", {
    status: agg.status,
    keys: agg.body && typeof agg.body === "object" ? Object.keys(agg.body).slice(0, 40) : null,
    has_segmented_top_level: Boolean(agg.body?.segmented_background),
  });
  const vals = pd.body?.canonical_values || pd.body?.product_definition?.canonical_values || {};
  writeJson("pd_canonical_keys.json", {
    keys: Object.keys(vals || {}),
    segmented: vals.segmented_background || null,
    segmented_proposal: vals.segmented_background_proposal || null,
    elec_draft: vals.electrical_connection_management_draft || vals.segmented_background?.electrical_connection_management_draft || null,
  });

  // Hidden error scan from API hits
  const badApi = apiHits.filter((h) => h.status >= 400);
  writeJson("api_hits_sample.json", { total: apiHits.length, bad: badApi.slice(0, 40), last20: apiHits.slice(-20) });
  if (badApi.length) note("HIGH", `API errors during walkthrough: ${badApi.length}`, { sample: badApi.slice(0, 8) });

  // Accessibility quick checks
  const a11y = await page.evaluate(() => {
    const tabs = [...document.querySelectorAll('[role="tab"]')];
    const unlabeled = [...document.querySelectorAll("button, select, input")]
      .filter((el) => {
        const aria = el.getAttribute("aria-label");
        const id = el.getAttribute("id");
        const label = id && document.querySelector(`label[for="${id}"]`);
        const text = (el.textContent || "").trim();
        return !aria && !label && text.length < 1 && el.tagName !== "INPUT";
      })
      .slice(0, 20)
      .map((el) => ({ tag: el.tagName, testid: el.getAttribute("data-testid"), type: el.getAttribute("type") }));
    return {
      tabRoles: tabs.length,
      tablist: Boolean(document.querySelector('[role="tablist"]')),
      unlabeledControls: unlabeled,
      overflowX: document.documentElement.scrollWidth > document.documentElement.clientWidth + 2,
    };
  });
  writeJson("a11y_quick.json", a11y);
  if (a11y.overflowX) note("MED", "Horizontal overflow detected on current page");
  if (a11y.unlabeledControls.length) note("MED", `Unlabeled controls: ${a11y.unlabeledControls.length}`);

  await page.close();
  return ws;
}

async function runSecondarySvgs(browser) {
  for (const [label, svg] of [
    ["cross", SVG_CROSS],
    ["sit3", SVG_SIT3],
  ]) {
    const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
    const ws = await createWorkspace(`audit-${label}`);
    writeJson(`workspace_${label}.json`, ws);
    await gotoOperator(page, ws.id);
    await importSvg(page, svg);
    await waitAnalysis(ws.id);
    await assignConturSuport(page);
    await page.waitForTimeout(2500);
    const proposal = await waitSeg(ws.id, ["PROPOSED", "CONFIRMED"], 30_000);
    writeJson(`proposal_${label}.json`, proposal);
    await advanceToReview(page);
    await goReviewTab(page, "montaj");
    await page.waitForTimeout(1500);
    await shot(page, `20_${label}_montaj.png`, { fullPage: true });
    const panel = page.getByTestId("intake-v6-segmented-background-panel");
    const vis = await panel.isVisible().catch(() => false);
    note("INFO", `${label}: segmented panel=${vis} status=${proposal?.status}`);
    if (vis && label === "sit3") {
      // calm path — leave proposed or confirm if easy
      const en = await page.getByTestId("intake-v6-segmented-confirm").isEnabled().catch(() => false);
      if (en) {
        await page.getByTestId("intake-v6-segmented-confirm").click();
        await page.waitForTimeout(1500);
      }
      await shot(page, `21_${label}_after_action.png`, { fullPage: true });
    }
    if (vis && label === "cross") {
      // try inject crossing if needed then screenshot
      const snap = await getWorkspace(ws.id);
      const current = snap.payload?.finish_setup?.segmented_background;
      if (current?.status === "PROPOSED" && !(current.element_bindings || []).length) {
        const panels = current.panels || [];
        if (panels.length >= 2) {
          const finish = {
            ...(snap.payload.finish_setup || {}),
            segmented_background: {
              ...current,
              element_bindings: [
                {
                  binding_id: "eb_audit_cross",
                  element_ref: "letter_over_joint",
                  construction_type: "APPLIED_VOLUMETRIC_LETTER",
                  primary_panel_id: panels[0].panel_id,
                  secondary_panel_id: panels[1].panel_id,
                  crosses_joint: true,
                  joint_id: (current.joints || [])[0]?.joint_id,
                  applied_component_template_code: "TPL-VOLUMETRIC-FACE_v1",
                },
              ],
            },
          };
          const put = await putFinish(ws.id, finish);
          writeJson("cross_binding_put.json", put);
          await page.reload({ waitUntil: "domcontentloaded" });
          await waitAuth(page);
          await goReviewTab(page, "montaj");
          await page.waitForTimeout(1200);
        }
      }
      await shot(page, "22_cross_applied_crossing.png", { fullPage: true });
    }
    await page.close();
  }
}

async function main() {
  for (const f of [SVG_BASIC, SVG_CROSS, SVG_SIT3]) {
    if (!fs.existsSync(f)) throw new Error(`Missing SVG: ${f}`);
    const st = fs.statSync(f);
    note("INFO", `SVG ok ${path.basename(f)} bytes=${st.size}`);
  }
  writeJson("preflight_svgs.json", {
    dir: DESKTOP,
    files: [SVG_BASIC, SVG_CROSS, SVG_SIT3].map((f) => ({
      path: f,
      bytes: fs.statSync(f).size,
    })),
  });

  const browser = await chromium.launch({ headless: true });
  try {
    await runPrimaryFlow(browser);
    await runSecondarySvgs(browser);
  } finally {
    await browser.close();
  }
  writeJson("findings.json", findings);
  console.log("DONE findings=", findings.length);
}

main().catch((err) => {
  console.error(err);
  writeJson("fatal.json", { message: String(err), stack: err?.stack });
  process.exit(1);
});
