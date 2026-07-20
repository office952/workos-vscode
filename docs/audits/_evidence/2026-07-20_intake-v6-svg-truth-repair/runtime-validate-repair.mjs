/**
 * Runtime proof for INTAKE_V6_SVG_TRUTH_CONTRACT_REPAIR_V1
 * Clean workspaces; Desktop SVG fixtures unmodified.
 */
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";
import fs from "node:fs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(path.join(__dirname, "../../../../frontend/package.json"));
const { chromium } = require("playwright");

const BACKEND = process.env.PW_BACKEND_URL ?? "http://127.0.0.1:8001";
const UI = process.env.PW_BASE_URL ?? "http://127.0.0.1:3000";
const DESKTOP = path.join(process.env.USERPROFILE || "", "Desktop", "fisiere-teste-svg");
const OUT = __dirname;

const CASES = [
  {
    id: "acm",
    file: path.join(DESKTOP, "litere-cu-fundal-acm-segmentat.svg"),
    expectSupport: true,
    expectLogoSupport: false,
    expectMinPanels: 2,
    expectArtworkMin: 0,
    expectArtworkMax: 0,
  },
  {
    id: "gradi",
    file: path.join(DESKTOP, "gradi-curat.svg"),
    expectSupport: false,
    expectLogoSupport: false,
    expectMinPanels: 0,
    expectArtworkMin: 2,
    expectArtworkMax: 10,
  },
];

async function createWorkspace(title) {
  const r = await fetch(`${BACKEND}/api/v1/intake-v6/workspaces`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, analyzer_mode: "analyzer_first" }),
  });
  if (!r.ok) throw new Error(`create ${r.status}`);
  return r.json();
}

async function getWorkspace(id) {
  const r = await fetch(`${BACKEND}/api/v1/intake-v6/workspaces/${id}`);
  if (!r.ok) throw new Error(`get ${r.status}`);
  return r.json();
}

async function waitSeg(id, timeoutMs = 45000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    const ws = await getWorkspace(id);
    const seg = ws.payload?.finish_setup?.segmented_background;
    if (seg && seg.status) return seg;
    await new Promise((r) => setTimeout(r, 800));
  }
  return null;
}

async function runCase(browser, c) {
  const dir = path.join(OUT, c.id);
  fs.mkdirSync(dir, { recursive: true });
  const ws = await createWorkspace(`Repair V1 ${c.id} ${Date.now()}`);
  const log = { case: c.id, workspaceId: ws.id, workspaceCode: ws.workspace_code, checks: [] };

  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  await ctx.addInitScript(() => {
    try {
      sessionStorage.setItem("WORKOS_DEV_GUARD_BYPASS", "1");
    } catch {
      /* ignore */
    }
  });
  const page = await ctx.newPage();
  await page.goto(`${UI}/intake-v6/${ws.id}/operator`, { waitUntil: "domcontentloaded", timeout: 120000 });
  await page.waitForTimeout(2000);
  await page.getByTestId("intake-v6-header").waitFor({ state: "visible", timeout: 90000 });
  await page.screenshot({ path: path.join(dir, "01-before-upload.png") });

  await page.getByTestId("intake-v6-svg-input").setInputFiles(c.file);
  await page.getByTestId("intake-v6-file-confirm-chip").waitFor({ state: "visible", timeout: 90000 });
  await page.screenshot({ path: path.join(dir, "02-after-upload.png") });

  // Confirm all
  const confirmAll = page.getByTestId("intake-v6-confirm-all-roles");
  if (await confirmAll.isVisible().catch(() => false)) {
    await confirmAll.click();
    await page.waitForTimeout(2500);
  }
  await page.screenshot({ path: path.join(dir, "03-after-confirm-all.png") });

  let seg = null;
  if (c.expectSupport) {
    seg = await waitSeg(ws.id, 45000);
    log.checks.push({
      name: "segmented_status",
      pass: Boolean(seg?.status && seg.status !== "null"),
      status: seg?.status ?? null,
      panels: seg?.panels?.length ?? 0,
    });
  } else {
    const snap = await getWorkspace(ws.id);
    seg = snap.payload?.finish_setup?.segmented_background ?? null;
    const hasSupportRole = (snap.payload?.layer_role_setup?.layers || []).some(
      (l) => l.confirmed_role === "support_panel",
    );
    log.checks.push({
      name: "no_support_panel_on_gradi",
      pass: !hasSupportRole,
      hasSupportRole,
    });
  }

  // Advance to review if possible
  const next = page.getByTestId("intake-v6-footer-next");
  if (await next.isEnabled().catch(() => false)) {
    await next.click();
    await page.waitForTimeout(2000);
  }
  await page.screenshot({ path: path.join(dir, "04-config.png") });

  // Reopen Straturi (P7)
  await page.getByTestId("intake-v6-progress-step-layers").click();
  await page.waitForTimeout(1500);
  // Survive a soft reload of workspace by clicking again if needed
  let chip = await page.getByTestId("intake-v6-file-confirm-chip").textContent().catch(() => null);
  let layers = await page.locator('[data-testid^="intake-v6-layer-row-"]').count();
  if (!chip || layers === 0) {
    await page.getByTestId("intake-v6-progress-step-layers").click();
    await page.waitForTimeout(1500);
    chip = await page.getByTestId("intake-v6-file-confirm-chip").textContent().catch(() => null);
    layers = await page.locator('[data-testid^="intake-v6-layer-row-"]').count();
  }
  await page.screenshot({ path: path.join(dir, "05-reopen-layers.png") });
  log.checks.push({
    name: "reopen_layers",
    pass: Boolean(chip) && layers > 0,
    chip,
    layers,
  });

  // Hard refresh while intending layers
  await page.reload({ waitUntil: "domcontentloaded" });
  await page.waitForTimeout(2500);
  await page.getByTestId("intake-v6-progress-step-layers").click().catch(() => {});
  await page.waitForTimeout(1500);
  chip = await page.getByTestId("intake-v6-file-confirm-chip").textContent().catch(() => null);
  layers = await page.locator('[data-testid^="intake-v6-layer-row-"]').count();
  await page.screenshot({ path: path.join(dir, "06-after-refresh-layers.png") });
  log.checks.push({
    name: "refresh_then_layers",
    pass: Boolean(chip) && layers > 0,
    chip,
    layers,
  });

  const finalWs = await getWorkspace(ws.id);
  const analysis = finalWs.payload?.svg_analysis_json;
  const roles = finalWs.payload?.layer_role_setup?.layers || [];
  const artwork = finalWs.payload?.finish_setup?.artwork_finishes || [];
  const supportRoles = roles.filter((l) => l.confirmed_role === "support_panel");
  const logoAsSupport = roles.filter(
    (l) =>
      String(l.layer_key || "").includes("logo") && l.confirmed_role === "support_panel",
  );

  log.payload = {
    readiness: finalWs.readiness_status,
    layerCount: analysis?.layers?.length,
    supportRoles: supportRoles.map((l) => l.layer_key),
    logoAsSupport: logoAsSupport.map((l) => l.layer_key),
    artworkCount: Array.isArray(artwork) ? artwork.length : 0,
    segmented: finalWs.payload?.finish_setup?.segmented_background?.status ?? null,
    panels: finalWs.payload?.finish_setup?.segmented_background?.panels?.length ?? 0,
    provenanceSample: (analysis?.layers || [])
      .filter((l) => (l.sourceGroupIds || []).length)
      .map((l) => ({ id: l.id, sourceGroupIds: l.sourceGroupIds, elementIds: l.elementIds })),
  };

  log.checks.push({
    name: "logo_not_support",
    pass: logoAsSupport.length === 0,
  });
  if (c.expectSupport) {
    log.checks.push({
      name: "has_support_assembly",
      pass: supportRoles.length >= 1,
    });
    log.checks.push({
      name: "panels_geometries",
      pass: (log.payload.panels || 0) >= c.expectMinPanels,
      panels: log.payload.panels,
    });
  }
  log.checks.push({
    name: "artwork_bounds",
    pass:
      log.payload.artworkCount >= c.expectArtworkMin &&
      log.payload.artworkCount <= c.expectArtworkMax,
    artworkCount: log.payload.artworkCount,
  });

  log.pass = log.checks.every((x) => x.pass);
  fs.writeFileSync(path.join(dir, "runtime-log.json"), JSON.stringify(log, null, 2));
  await ctx.close();
  return log;
}

async function main() {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const results = [];
  for (const c of CASES) {
    console.log("RUN", c.id);
    const log = await runCase(browser, c);
    results.push(log);
    console.log(c.id, log.pass ? "PASS" : "FAIL", JSON.stringify(log.checks));
  }
  await browser.close();
  fs.writeFileSync(path.join(OUT, "runtime-summary.json"), JSON.stringify(results, null, 2));
  if (!results.every((r) => r.pass)) process.exit(1);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
