/**
 * Read-only API walker: SVG → roles → bindings → composition → PD signals.
 * Runtime: FE proxy :3000 → BE :8003. Docs evidence only — no domain mutation beyond
 * create/upload/persist needed to observe analyzer truth (standard audit path).
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
const FIXTURE_DIR = "C:/Users/offic/Desktop/fisiere-teste-svg";
const HEAD = "f39c260";

fs.mkdirSync(OUT, { recursive: true });
fs.mkdirSync(SHOTS, { recursive: true });

const FIXTURES = [
  { id: "acm_segmented", file: "litere-cu-fundal-acm-segmentat.svg" },
  { id: "acm_crossing", file: "litere-cu-fundal-acm-segmentat-litera-peste-imbinare.svg" },
  { id: "situatie_3", file: "situatie-3.svg" },
  { id: "simple_letters", file: "litere-vol-1-layer.svg" },
];

function writeJson(name, data) {
  fs.writeFileSync(path.join(OUT, name), JSON.stringify(data, null, 2));
}

async function apiJson(url, options = {}) {
  const res = await fetch(url, options);
  const text = await res.text();
  let body;
  try {
    body = JSON.parse(text);
  } catch {
    body = { raw: text.slice(0, 2000) };
  }
  return { status: res.status, body };
}

async function createWorkspace(title) {
  return apiJson(`${API}/workspaces`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      title,
      selected_template_code: "TPL-VOLUMETRIC-LETTERS_v2",
      analyzer_mode: "analyzer_first",
    }),
  });
}

async function uploadSvg(workspaceId, filePath) {
  const buf = fs.readFileSync(filePath);
  const form = new FormData();
  form.append("file", new Blob([buf], { type: "image/svg+xml" }), path.basename(filePath));
  const res = await fetch(`${API}/workspaces/${workspaceId}/svg`, { method: "POST", body: form });
  const text = await res.text();
  let body;
  try {
    body = JSON.parse(text);
  } catch {
    body = { raw: text.slice(0, 2000) };
  }
  return { status: res.status, body };
}

function summarizeWorkspace(ws) {
  const p = ws?.payload ?? {};
  const finish = p.finish_setup ?? {};
  const layers = p.path_geometry_summary?.layers ?? [];
  const roleSetup = p.layer_role_setup ?? p.layer_role_review ?? null;
  const rec = p.product_composition_recommendation ?? null;
  const confirmed = p.product_composition_confirmed ?? null;
  const bindings = Array.isArray(finish.svg_component_bindings)
    ? finish.svg_component_bindings
    : [];
  const seg = finish.segmented_background ?? null;
  const support = finish.svg_support_selection ?? null;
  return {
    id: ws?.id,
    workspace_code: ws?.workspace_code,
    title: ws?.title,
    template_code: ws?.template_code,
    readiness_status: ws?.readiness_status,
    layer_count: layers.length,
    layers: layers.map((l) => ({
      key: l.layer_key ?? l.key ?? l.id,
      name: l.layer_name ?? l.name,
      role_hint: l.auto_role ?? l.role ?? l.suggested_role,
      closed: l.closed_path_count ?? l.closed_count,
      open: l.open_path_count ?? l.open_count,
    })),
    role_setup_status: roleSetup?.confirmation_status ?? roleSetup?.confirmationStatus ?? null,
    role_layers: (roleSetup?.layers ?? []).map((l) => ({
      key: l.layer_key ?? l.layerKey,
      auto: l.auto_role ?? l.autoRole,
      confirmed: l.confirmed_role ?? l.confirmedRole,
      state: l.confirmation_state ?? l.confirmationState,
      label: l.display_label ?? l.displayLabel ?? l.layer_name,
    })),
    composition_items: (rec?.composition_items ?? []).map((i) => ({
      key: i.item_key ?? i.key,
      label: i.display_name ?? i.label,
      template: i.template_code ?? i.component_template_code,
      status: i.status,
      source: i.source,
    })),
    composition_confirmed: Boolean(confirmed?.confirmed),
    bindings: bindings.map((b) => ({
      role: b.geometry_role,
      template: b.component_template_code,
      status: b.status,
      layers: b.selected_geometry?.layer_ids ?? [],
      provenance: b.provenance,
      face_treatment: b.face_treatment_code,
    })),
    support_selection: support
      ? {
          status: support.status,
          contour_id: support.contour_id,
          role: support.role,
        }
      : null,
    segmented: seg
      ? {
          status: seg.status,
          panel_count: Array.isArray(seg.panels) ? seg.panels.length : seg.panel_count,
          host: seg.host_component_template_code ?? seg.meta?.host_template,
        }
      : null,
    product_truth_components: p.product_truth?.components
      ? Object.keys(p.product_truth.components)
      : [],
  };
}

async function getPd(workspaceId) {
  // Product definition preview endpoints used by Intake
  const urls = [
    `${UI}/api/v1/product-system/product-definition/TPL-VOLUMETRIC-LETTERS_v2?workspace_id=${workspaceId}`,
    `${API}/workspaces/${workspaceId}/product-definition-preview`,
    `${API}/workspaces/${workspaceId}/pre-order-technical-preview`,
  ];
  const out = {};
  for (const url of urls) {
    const key = url.includes("product-definition/")
      ? "pd_letters"
      : url.includes("product-definition-preview")
        ? "pd_preview"
        : "pre_order_preview";
    out[key] = await apiJson(url);
  }
  return out;
}

async function walkFixture(fixture, browser) {
  const filePath = path.join(FIXTURE_DIR, fixture.file);
  if (!fs.existsSync(filePath)) {
    return { fixture, error: "missing_file", filePath };
  }
  const created = await createWorkspace(`wiring-audit-${fixture.id}-${Date.now()}`);
  if (created.status !== 200 && created.status !== 201) {
    return { fixture, error: "create_failed", created };
  }
  const wsId = created.body.id;
  const uploaded = await uploadSvg(wsId, filePath);
  writeJson(`${fixture.id}_upload.json`, uploaded);
  const afterUpload = await apiJson(`${API}/workspaces/${wsId}`);
  writeJson(`${fixture.id}_workspace_after_upload.json`, afterUpload.body);
  const summary = summarizeWorkspace(afterUpload.body);
  const pd = await getPd(wsId);
  writeJson(`${fixture.id}_pd_bundle.json`, pd);

  // UI walk
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  const url = `${UI}/intake-v6/${wsId}/operator`;
  await page.goto(url, { waitUntil: "domcontentloaded", timeout: 120000 });
  await page.waitForTimeout(2500);
  await page.screenshot({ path: path.join(SHOTS, `${fixture.id}_01_page1_after_upload.png`) });

  // Capture role labels visible
  const page1Probe = await page.evaluate(() => {
    const text = document.body.innerText;
    const roleSelects = [...document.querySelectorAll('[data-testid^="intake-v6-layer-role-"]')].map(
      (el) => ({
        testId: el.getAttribute("data-testid"),
        value: el.value ?? el.textContent?.trim()?.slice(0, 80),
        selectedText: el.selectedOptions?.[0]?.textContent ?? null,
      }),
    );
    return {
      hasVectorLitere: /Vector Litere/i.test(text),
      hasVectorLogo: /Vector Logo/i.test(text),
      hasSupport: /Fundal|suport|Alucobond|Contur suport/i.test(text),
      hasLitereVolumetrice: /Litere volumetrice/i.test(text),
      stepCurrent: document
        .querySelector('[data-testid="intake-v6-progress-step-layers"][aria-current="step"], [data-testid="intake-v6-progress-step-layers"][data-active="true"], button[aria-current="true"]')
        ?.getAttribute("data-testid"),
      roleSelects,
      url: location.href,
    };
  });
  writeJson(`${fixture.id}_page1_probe.json`, page1Probe);

  // Role change experiment: if a role select exists, change first non-support to support or vice versa and watch navigation
  const roleSelect = page.locator('[data-testid^="intake-v6-layer-role-"]').first();
  let navProbe = { skipped: true };
  if ((await roleSelect.count()) > 0) {
    const beforeUrl = page.url();
    const beforeStep = await page.evaluate(() => ({
      layers: !!document.querySelector('[data-testid="intake-v6-progress-step-layers"][aria-current="step"], [data-testid="intake-v6-progress-step-layers"][data-state="active"]'),
      review: document.querySelector('[data-testid="intake-v6-progress-step-review"]')?.getAttribute("aria-current"),
      confirm: document.querySelector('[data-testid="intake-v6-progress-step-confirm"]')?.getAttribute("aria-current"),
      href: location.href,
    }));
    const options = await roleSelect.locator("option").allTextContents();
    // Toggle to a different role if possible
    const current = await roleSelect.inputValue();
    const candidates = ["face", "printed_artwork", "support_panel", "ignore"];
    const next = candidates.find((c) => c !== current) ?? current;
    await roleSelect.selectOption(next).catch(() => null);
    await page.waitForTimeout(1200);
    const afterStep = await page.evaluate(() => ({
      layersCurrent: document.querySelector('[data-testid="intake-v6-progress-step-layers"]')?.getAttribute("aria-current"),
      reviewCurrent: document.querySelector('[data-testid="intake-v6-progress-step-review"]')?.getAttribute("aria-current"),
      confirmCurrent: document.querySelector('[data-testid="intake-v6-progress-step-confirm"]')?.getAttribute("aria-current"),
      href: location.href,
      bodyHasConfirmare: /Confirmare/i.test(document.body.innerText),
    }));
    navProbe = {
      skipped: false,
      beforeUrl,
      beforeStep,
      changedFrom: current,
      changedTo: next,
      options,
      afterStep,
      navigatedAwayFromLayers: afterStep.href !== beforeUrl || afterStep.confirmCurrent === "step" || afterStep.reviewCurrent === "step",
    };
    await page.screenshot({ path: path.join(SHOTS, `${fixture.id}_02_after_role_select.png`) });
  }

  // Persist / continue if button exists
  const continueBtn = page.getByRole("button", { name: /Continuă|Salvează|Confirmă rol/i }).first();
  if ((await continueBtn.count()) > 0) {
    await continueBtn.click({ force: true }).catch(() => null);
    await page.waitForTimeout(1500);
  }

  // Try review tabs
  const review = page.getByTestId("intake-v6-progress-step-review");
  if ((await review.count()) > 0) {
    await review.click({ force: true }).catch(() => null);
    await page.waitForTimeout(1500);
  }
  for (const [tab, shot] of [
    ["finisaje", `${fixture.id}_03_page2_finisaje.png`],
    ["iluminare", `${fixture.id}_04_page2_iluminare.png`],
    ["montaj", `${fixture.id}_05_page2_montaj.png`],
  ]) {
    const t = page.getByTestId(`intake-v6-review-tab-${tab}`);
    if ((await t.count()) > 0) {
      await t.click({ force: true }).catch(() => null);
      await page.waitForTimeout(800);
      await page.screenshot({ path: path.join(SHOTS, shot) });
    }
  }

  const page2Probe = await page.evaluate(() => {
    const text = document.body.innerText;
    return {
      href: location.href,
      hasLetterCluster: !!document.querySelector('[data-testid="intake-v6-letter-group-face-finishes"]'),
      hasArtwork: !!document.querySelector('[data-testid="intake-v6-artwork-finishes"]'),
      hasLighting: !!document.querySelector('[data-testid="intake-v6-review-lighting-section"]'),
      hasSegmented: /segmentar|panouri|Alucobond|fundal/i.test(text),
      hasOracal: /Oracal/i.test(text),
      hasFold: /pliere|fold|L1|L2|adâncime caset/i.test(text),
      hasVectorLitere: /Vector Litere|Litere volumetrice/i.test(text),
      montajVisible: !!document.querySelector('[data-testid="intake-v6-review-tab-panel-montaj"]'),
    };
  });
  writeJson(`${fixture.id}_page2_probe.json`, page2Probe);

  const confirm = page.getByTestId("intake-v6-progress-step-confirm");
  if ((await confirm.count()) > 0) {
    await confirm.click({ force: true }).catch(() => null);
    await page.waitForTimeout(1200);
    await page.screenshot({ path: path.join(SHOTS, `${fixture.id}_06_confirmare.png`) });
  }

  // Reload persistence check
  await page.reload({ waitUntil: "domcontentloaded" });
  await page.waitForTimeout(2000);
  await page.screenshot({ path: path.join(SHOTS, `${fixture.id}_07_reload.png`) });
  const reloaded = await apiJson(`${API}/workspaces/${wsId}`);
  writeJson(`${fixture.id}_workspace_reload.json`, summarizeWorkspace(reloaded.body));

  await page.close();

  return {
    fixture,
    workspace_id: wsId,
    url: `${UI}/intake-v6/${wsId}/operator`,
    head_expected: HEAD,
    summary,
    page1Probe,
    navProbe,
    page2Probe,
    pd_status: {
      pd_letters: pd.pd_letters?.status,
      pd_preview: pd.pd_preview?.status,
      pre_order_preview: pd.pre_order_preview?.status,
    },
    templates_in_bindings: summary.bindings.map((b) => b.template),
    face_present: summary.bindings.some((b) => b.template === "TPL-VOLUMETRIC-FACE_v1"),
    acm_present: summary.bindings.some((b) => b.template === "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1"),
  };
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const results = [];
  for (const fixture of FIXTURES) {
    console.log("walking", fixture.id);
    try {
      const r = await walkFixture(fixture, browser);
      results.push(r);
      writeJson(`${fixture.id}_result.json`, r);
      console.log(
        "done",
        fixture.id,
        "ws=",
        r.workspace_id,
        "face=",
        r.face_present,
        "acm=",
        r.acm_present,
        "navAway=",
        r.navProbe?.navigatedAwayFromLayers,
      );
    } catch (err) {
      console.error(fixture.id, err);
      results.push({ fixture, error: String(err) });
    }
  }
  await browser.close();

  // Bindables registry snapshot from availability API
  const avail = await apiJson(
    `${UI}/api/v1/product-system/product-templates/availability?product_template_code=TPL-VOLUMETRIC-LETTERS_v2`,
  ).catch(() => null);
  if (!avail || avail.status >= 400) {
    const avail2 = await apiJson(`${UI}/api/v1/product-system/templates/availability`);
    writeJson("availability_fallback.json", avail2);
  } else {
    writeJson("availability_letters.json", avail);
  }

  const served = {
    at: new Date().toISOString(),
    ui: UI,
    expected_head: HEAD,
    note: "After screenshots for letter pilot closed on :3000; this audit uses same stack. :3001 crash 3221226505 operational only.",
    fixtures_found: FIXTURES.map((f) => ({
      ...f,
      exists: fs.existsSync(path.join(FIXTURE_DIR, f.file)),
    })),
    results: results.map((r) => ({
      id: r.fixture?.id,
      workspace_id: r.workspace_id,
      face: r.face_present,
      acm: r.acm_present,
      navAway: r.navProbe?.navigatedAwayFromLayers,
      bindings: r.summary?.bindings,
      role_layers: r.summary?.role_layers,
      composition_items: r.summary?.composition_items,
      page2: r.page2Probe,
      error: r.error,
    })),
  };
  writeJson("audit_summary.json", served);
  console.log("SUMMARY", JSON.stringify(served.results, null, 2));
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
