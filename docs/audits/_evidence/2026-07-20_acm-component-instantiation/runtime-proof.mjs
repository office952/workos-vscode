/**
 * Runtime proof — INTAKE_V6_ACM_COMPONENT_INSTANTIATION_AND_RELATIONSHIP_V1
 * Clean workspace; no historic writes.
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
const SVG = path.join(
  process.env.USERPROFILE || "",
  "Desktop",
  "fisiere-teste-svg",
  "litere-cu-fundal-acm-segmentat.svg",
);
const OUT = __dirname;

async function createWorkspace(title) {
  const r = await fetch(`${BACKEND}/api/v1/intake-v6/workspaces`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, analyzer_mode: "analyzer_first" }),
  });
  if (!r.ok) throw new Error(`create ${r.status} ${await r.text()}`);
  return r.json();
}

async function getWorkspace(id) {
  const r = await fetch(`${BACKEND}/api/v1/intake-v6/workspaces/${id}`);
  if (!r.ok) throw new Error(`get ${r.status}`);
  return r.json();
}

function inspectPayload(ws) {
  const fs = ws.payload?.finish_setup || {};
  const bindings = fs.svg_component_bindings || [];
  const support = bindings.filter((b) => b.geometry_role === "SUPPORT_CONTOUR");
  const sel = fs.svg_support_selection || {};
  const inst =
    fs.acm_panel_instance ||
    fs.svg_support_selection?.acm_panel_instance ||
    fs.mounting_solution?.configuration?.acm_panel_instance ||
    null;
  const seg = fs.segmented_background || null;
  const compConf = ws.payload?.product_composition_confirmed || null;
  const compRec = ws.payload?.product_composition_recommendation || null;
  const artwork = fs.artwork_finishes || [];
  return {
    workspace_code: ws.workspace_code,
    id: ws.id,
    supportBindingCount: support.length,
    supportBindingStatus: support[0]?.status ?? null,
    selectionStatus: sel.status ?? null,
    associationStatus: inst?.association_status ?? sel.association_status ?? null,
    technicalStatus: inst?.technical_configuration_status ?? sel.technical_configuration_status ?? null,
    compositionStatusInstance: inst?.composition_status ?? null,
    compositionConfirmed: Boolean(compConf?.confirmed),
    compositionType: compRec?.composition_type ?? null,
    compositionItems: (compRec?.composition_items || []).map((i) => i.template_code),
    hasMounting: Boolean(fs.mounting_solution?.template_code || fs.mounting_solution?.kind),
    mountingTemplate: fs.mounting_solution?.template_code ?? null,
    segStatus: seg?.status ?? null,
    segPanels: seg?.panels?.length ?? 0,
    instanceId: inst?.component_instance_id ?? null,
    domainAction: fs.acm_panel_domain_action ?? null,
    relations:
      inst?.relations ||
      fs.svg_support_selection?.component_relations ||
      seg?.meta?.component_relations ||
      [],
    fieldAuthority: sel.field_authority || inst?.configuration?.field_authority || null,
    artworkCount: artwork.length,
    capabilities: inst?.capabilities ?? null,
  };
}

async function main() {
  fs.mkdirSync(OUT, { recursive: true });
  if (!fs.existsSync(SVG)) throw new Error(`missing fixture ${SVG}`);

  const ws = await createWorkspace(`ACM Instantiation V1 ${Date.now()}`);
  const report = { workspaceId: ws.id, workspaceCode: ws.workspace_code, checks: [], pass: true };

  const browser = await chromium.launch({ headless: true });
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
  await page.getByTestId("intake-v6-header").waitFor({ state: "visible", timeout: 90000 });
  await page.screenshot({ path: path.join(OUT, "01-before-upload.png"), fullPage: false });

  await page.getByTestId("intake-v6-svg-input").setInputFiles(SVG);
  await page.getByTestId("intake-v6-file-confirm-chip").waitFor({ state: "visible", timeout: 90000 });
  await page.screenshot({ path: path.join(OUT, "02-after-upload.png") });

  const confirmAll = page.getByTestId("intake-v6-confirm-all-roles");
  await confirmAll.waitFor({ state: "visible", timeout: 30000 });
  await confirmAll.click();
  await page.waitForTimeout(4000);
  await page.screenshot({ path: path.join(OUT, "03-after-confirm-all.png") });

  // Wait for ACM shell
  let snap = null;
  for (let i = 0; i < 40; i++) {
    const w = await getWorkspace(ws.id);
    snap = inspectPayload(w);
    if (snap.supportBindingCount >= 1 && snap.selectionStatus && snap.hasMounting) break;
    await new Promise((r) => setTimeout(r, 500));
  }
  fs.writeFileSync(path.join(OUT, "payload-after-roles.json"), JSON.stringify(snap, null, 2));

  const check = (name, pass, detail) => {
    report.checks.push({ name, pass, ...detail });
    if (!pass) report.pass = false;
  };

  check("support_binding", snap.supportBindingCount >= 1, { count: snap.supportBindingCount });
  check("selection_proposed_not_confirmed", snap.selectionStatus === "proposed", {
    status: snap.selectionStatus,
  });
  check("mounting_present", snap.hasMounting, { template: snap.mountingTemplate });
  check("segmented_proposed", snap.segStatus === "PROPOSED" && snap.segPanels >= 2, {
    status: snap.segStatus,
    panels: snap.segPanels,
  });
  check("acm_instance", Boolean(snap.instanceId), { id: snap.instanceId });
  check("association_proposed", snap.associationStatus === "proposed", {
    status: snap.associationStatus,
  });
  check("technical_proposed", snap.technicalStatus === "proposed", { status: snap.technicalStatus });
  check("composition_not_auto_confirmed", snap.compositionConfirmed === false, {
    confirmed: snap.compositionConfirmed,
    instanceComposition: snap.compositionStatusInstance,
  });
  check("catalog_defaults_tagged", snap.fieldAuthority?.acm_thickness_mm === "catalog_default", {
    auth: snap.fieldAuthority,
  });
  check("zero_phantom_artwork", snap.artworkCount === 0, { artworkCount: snap.artworkCount });
  const hasAutoMount = (snap.relations || []).some(
    (r) =>
      (r.relation_type === "mounts_on" || r.relation_type === "attached_to_structure") &&
      r.provenance !== "operator",
  );
  check("no_auto_mounts_on", !hasAutoMount, { relations: snap.relations?.length });

  // Explicit composition confirm (never auto)
  const compToggle = page.getByTestId("intake-v6-product-composition-toggle");
  if (await compToggle.isVisible().catch(() => false)) {
    const expanded = await compToggle.getAttribute("aria-expanded");
    if (expanded !== "true") await compToggle.click();
    await page.waitForTimeout(500);
  }
  const compBtn = page.getByTestId("intake-v6-confirm-product-composition");
  if (await compBtn.isVisible().catch(() => false)) {
    await compBtn.click();
    await page.waitForTimeout(2000);
  }
  await page.screenshot({ path: path.join(OUT, "04-after-composition-confirm.png") });

  let afterComp = inspectPayload(await getWorkspace(ws.id));
  check("composition_confirmed_after_operator", afterComp.compositionConfirmed === true, {
    confirmed: afterComp.compositionConfirmed,
  });

  // Refresh + reopen Straturi
  await page.reload({ waitUntil: "domcontentloaded" });
  await page.getByTestId("intake-v6-header").waitFor({ state: "visible", timeout: 90000 });
  await page.waitForTimeout(1500);
  const layersTab = page.getByRole("button", { name: /straturi|layers/i }).first();
  if (await layersTab.isVisible().catch(() => false)) {
    await layersTab.click();
    await page.waitForTimeout(1000);
  }
  await page.screenshot({ path: path.join(OUT, "05-after-refresh-layers.png") });

  const afterRefresh = inspectPayload(await getWorkspace(ws.id));
  fs.writeFileSync(path.join(OUT, "payload-after-refresh.json"), JSON.stringify(afterRefresh, null, 2));
  check("persist_support_after_refresh", afterRefresh.supportBindingCount >= 1, afterRefresh);
  check("persist_mounting_after_refresh", afterRefresh.hasMounting, {
    mounting: afterRefresh.mountingTemplate,
  });
  check("persist_panels_after_refresh", afterRefresh.segPanels >= 2, {
    panels: afterRefresh.segPanels,
  });
  check("persist_instance_after_refresh", Boolean(afterRefresh.instanceId), {
    id: afterRefresh.instanceId,
  });

  report.afterRoles = snap;
  report.afterComposition = afterComp;
  report.afterRefresh = afterRefresh;
  fs.writeFileSync(path.join(OUT, "runtime-summary.json"), JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report, null, 2));
  await browser.close();
  if (!report.pass) process.exit(1);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
