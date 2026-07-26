/**
 * Runtime audit capture — Intake V6 with real Desktop SVG fixtures.
 * Two clean sessions; no mocks; no SVG mutation.
 *
 * Prerequisites: FE :3000, BE :8001 (npm run dev:backend / Vite proxy).
 */
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";
import fs from "node:fs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(path.join(__dirname, "../../../../frontend/package.json"));
const { chromium } = require("playwright");

const OUT = __dirname;
const BACKEND = process.env.PW_BACKEND_URL ?? "http://127.0.0.1:8001";
const UI = process.env.PW_BASE_URL ?? "http://127.0.0.1:3000";
const VIEWPORT = { width: 1440, height: 900 };
const DESKTOP_SVG = path.join(
  process.env.USERPROFILE || process.env.HOME || "",
  "Desktop",
  "fisiere-teste-svg",
);

const CASES = [
  {
    id: "case1-acm-segmentat",
    label: "litere-cu-fundal-acm-segmentat",
    file: path.join(DESKTOP_SVG, "litere-cu-fundal-acm-segmentat.svg"),
  },
  {
    id: "case2-gradi-curat",
    label: "gradi-curat",
    file: path.join(DESKTOP_SVG, "gradi-curat.svg"),
  },
];

function ensureDir(p) {
  fs.mkdirSync(p, { recursive: true });
}

function writeJson(filePath, data) {
  fs.writeFileSync(filePath, JSON.stringify(data, null, 2), "utf8");
}

async function createWorkspace(title) {
  const response = await fetch(`${BACKEND}/api/v1/intake-v6/workspaces`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, analyzer_mode: "analyzer_first" }),
    signal: AbortSignal.timeout(20_000),
  });
  if (!response.ok) {
    throw new Error(`workspace create ${response.status}: ${(await response.text()).slice(0, 400)}`);
  }
  return response.json();
}

async function getWorkspace(id) {
  const response = await fetch(`${BACKEND}/api/v1/intake-v6/workspaces/${id}`, {
    signal: AbortSignal.timeout(20_000),
  });
  if (!response.ok) throw new Error(`workspace get ${response.status}`);
  return response.json();
}

async function waitAuth(page) {
  await page.getByText("Se verifică sesiunea").waitFor({ state: "hidden", timeout: 60_000 }).catch(() => {});
  await page.waitForTimeout(500);
}

async function shot(page, dir, name, { fullPage = false } = {}) {
  const file = fullPage ? `${name}-fullpage.png` : `${name}-1440x900.png`;
  await page.screenshot({ path: path.join(dir, file), fullPage });
  return file;
}

async function collectUiSnapshot(page) {
  return page.evaluate(() => {
    const text = (sel) => {
      const el = document.querySelector(sel);
      return el ? (el.textContent || "").replace(/\s+/g, " ").trim().slice(0, 500) : null;
    };
    const allText = (sel) =>
      Array.from(document.querySelectorAll(sel)).map((el) =>
        (el.textContent || "").replace(/\s+/g, " ").trim().slice(0, 200),
      );
    const attrs = (sel, attr) =>
      Array.from(document.querySelectorAll(sel)).map((el) => el.getAttribute(attr));

    return {
      url: location.href,
      fileChip: text('[data-testid="intake-v6-file-confirm-chip"]'),
      emptyAnalyzer: text('[data-testid="intake-v6-empty-analyzer-state"]'),
      error: text('[data-testid="intake-v6-error"]'),
      conturHint: text('[data-testid="intake-v6-contur-suport-hint"]'),
      conturError: text('[data-testid="intake-v6-contur-suport-error"]'),
      layersAllConfirmed: Boolean(document.querySelector('[data-testid="intake-v6-layers-all-confirmed"]')),
      layerRows: attrs('[data-testid^="intake-v6-layer-row-"]', "data-testid"),
      layerRoleSelects: Array.from(
        document.querySelectorAll('[data-testid^="intake-v6-layer-role-"]'),
      ).map((sel) => {
        const testId = sel.getAttribute("data-testid") || "";
        const selected = sel.value || "";
        const options = Array.from(sel.querySelectorAll("option")).map((o) => ({
          value: o.value,
          label: (o.textContent || "").trim(),
        }));
        return { testId, selected, options: options.slice(0, 20) };
      }),
      previewPresent: Boolean(document.querySelector('[data-testid="intake-v6-svg-preview"]')),
      previewInspect: Boolean(document.querySelector('[data-testid="intake-v6-preview-inspect-dialog"]')),
      geometrySummary: text('[data-testid="intake-v6-operator-geometry-summary"]') ||
        text('[data-testid="intake-v6-geometry-panel"]'),
      componentAssignment: text('[data-testid="intake-v6-svg-component-assignment"]'),
      bindableList: allText('[data-testid^="intake-v6-bindable-"]'),
      blockerBanner: text('[data-testid="intake-v6-operator-blocker-banner"]') ||
        text('[data-testid*="blocker"]'),
      warningTexts: allText(".text-amber-300, .text-yellow-300, [data-testid*='warning']").slice(0, 30),
      redTexts: allText(".text-red-300, .text-rose-300, [data-testid*='error']").slice(0, 30),
      header: text('[data-testid="intake-v6-header"]'),
      stepReview: Boolean(document.querySelector('[data-testid="intake-v6-step-review"]')),
      stepLayers: Boolean(document.querySelector('[data-testid="intake-v6-svg-analyzer-step"]')),
      busyLabelVisible: /Analizez/i.test(document.body.innerText || ""),
      bodySample: (document.body.innerText || "").replace(/\s+/g, " ").trim().slice(0, 1200),
    };
  });
}

async function summarizeWorkspacePayload(ws) {
  const payload = ws?.payload || {};
  const analysis = payload.svg_analysis_json || payload.svg_analysis || null;
  let analysisObj = analysis;
  if (typeof analysis === "string") {
    try {
      analysisObj = JSON.parse(analysis);
    } catch {
      analysisObj = { _rawLength: analysis.length };
    }
  }
  const layers =
    analysisObj?.layers ||
    analysisObj?.layer_summaries ||
    analysisObj?.report?.layers ||
    null;
  const geometry =
    analysisObj?.geometry ||
    analysisObj?.bounds ||
    analysisObj?.viewBox ||
    analysisObj?.report?.geometry ||
    null;

  return {
    id: ws.id,
    workspace_code: ws.workspace_code,
    title: ws.title,
    status: ws.status,
    readiness_status: ws.readiness_status,
    template_code: ws.template_code,
    has_svg_source: Boolean(payload.svg_source),
    svg_source_bytes: typeof payload.svg_source === "string" ? payload.svg_source.length : 0,
    has_svg_analysis: Boolean(analysis),
    analysis_keys: analysisObj && typeof analysisObj === "object" ? Object.keys(analysisObj).slice(0, 40) : [],
    layer_count_guess: Array.isArray(layers) ? layers.length : null,
    geometry_snippet: geometry,
    layer_role_setup: payload.layer_role_setup || null,
    file_name:
      payload.svg_file_name ||
      payload.source_file_name ||
      payload.uploaded_file_name ||
      analysisObj?.fileName ||
      analysisObj?.file_name ||
      null,
    segmented_background: payload.finish_setup?.segmented_background || null,
    blockers: ws.blockers || payload.blockers || null,
    warnings: ws.warnings || payload.warnings || null,
  };
}

async function runCase(browser, caseDef) {
  const dir = path.join(OUT, caseDef.id);
  ensureDir(dir);
  const log = {
    case: caseDef,
    startedAt: new Date().toISOString(),
    steps: [],
    problems: [],
    screenshots: [],
  };

  const note = (step, observed, expected = null, extra = {}) => {
    log.steps.push({ step, observed, expected, at: new Date().toISOString(), ...extra });
  };

  if (!fs.existsSync(caseDef.file)) {
    throw new Error(`SVG missing: ${caseDef.file}`);
  }
  const fileStat = fs.statSync(caseDef.file);
  note("fixture", `exists ${caseDef.file}`, null, { bytes: fileStat.size });

  const ws = await createWorkspace(`Audit SVG ${caseDef.label} ${Date.now()}`);
  log.workspaceId = ws.id;
  log.workspaceCode = ws.workspace_code;
  note("create_workspace", `created ${ws.id} / ${ws.workspace_code}`);

  const context = await browser.newContext({ viewport: VIEWPORT, deviceScaleFactor: 1 });
  await context.addInitScript(() => {
    try {
      sessionStorage.setItem("WORKOS_DEV_GUARD_BYPASS", "1");
    } catch {
      /* ignore */
    }
  });
  const page = await context.newPage();
  const consoleErrors = [];
  page.on("console", (msg) => {
    if (msg.type() === "error") consoleErrors.push(msg.text().slice(0, 300));
  });
  page.on("pageerror", (err) => consoleErrors.push(String(err).slice(0, 300)));

  // 1) Open Intake V6 before upload
  await page.goto(`${UI}/intake-v6/${ws.id}/operator`, {
    waitUntil: "domcontentloaded",
    timeout: 120_000,
  });
  await waitAuth(page);
  await page.getByTestId("intake-v6-header").waitFor({ state: "visible", timeout: 90_000 });
  log.screenshots.push(await shot(page, dir, "01-before-upload"));
  const beforeUi = await collectUiSnapshot(page);
  note("open_intake_v6", "workspace operator loaded", null, { ui: beforeUi });

  // Ensure layers step
  await page.getByTestId("intake-v6-progress-step-layers").click().catch(() => {});
  await page.waitForTimeout(800);
  log.screenshots.push(await shot(page, dir, "02-layers-before-upload"));

  const input = page.getByTestId("intake-v6-svg-input");
  await input.waitFor({ state: "attached", timeout: 60_000 });
  const selectBtn = page.getByTestId("intake-v6-svg-select-button");
  const selectVisible = await selectBtn.isVisible().catch(() => false);
  note("upload_control", selectVisible ? "select button visible" : "select button missing; input attached", null, {
    selectVisible,
    inputAttached: true,
  });

  // 2) Upload — capture mid-process if possible
  const uploadStarted = Date.now();
  const uploadPromise = input.setInputFiles(caseDef.file);
  // brief poll for busy state
  let sawBusy = false;
  for (let i = 0; i < 20; i += 1) {
    await page.waitForTimeout(50);
    const ui = await collectUiSnapshot(page);
    if (ui.busyLabelVisible) {
      sawBusy = true;
      log.screenshots.push(await shot(page, dir, "03-upload-processing"));
      break;
    }
  }
  await uploadPromise;
  note("upload_start", `setInputFiles done; sawBusy=${sawBusy}`, "feedback Analizez… during process");

  // Wait for result
  const chip = page.getByTestId("intake-v6-file-confirm-chip");
  const errEl = page.getByTestId("intake-v6-error");
  let uploadOk = false;
  let uploadError = null;
  try {
    await Promise.race([
      chip.waitFor({ state: "visible", timeout: 90_000 }).then(() => {
        uploadOk = true;
      }),
      errEl.waitFor({ state: "visible", timeout: 90_000 }).then(async () => {
        uploadError = ((await errEl.textContent()) || "").trim();
      }),
    ]);
  } catch (e) {
    uploadError = String(e);
  }
  const afterProcessMs = Date.now() - uploadStarted;
  log.screenshots.push(await shot(page, dir, "04-after-process"));
  const afterUi = await collectUiSnapshot(page);
  note(
    "after_process",
    uploadOk ? "file chip visible" : `upload failed/timeout: ${uploadError}`,
    "chip with correct filename + recognized SVG",
    { ms: afterProcessMs, ui: afterUi, uploadOk, uploadError },
  );

  // Preview
  const preview = page.getByTestId("intake-v6-svg-preview");
  const previewVisible = await preview.isVisible().catch(() => false);
  if (previewVisible) {
    await preview.scrollIntoViewIfNeeded().catch(() => {});
    log.screenshots.push(await shot(page, dir, "05-preview"));
  } else {
    // alternate test ids
    const alt = page.locator('[data-testid*="svg-preview"]').first();
    if (await alt.isVisible().catch(() => false)) {
      await alt.scrollIntoViewIfNeeded();
      log.screenshots.push(await shot(page, dir, "05-preview"));
    } else {
      log.screenshots.push(await shot(page, dir, "05-preview-missing"));
    }
  }
  note("preview", previewVisible ? "preview visible" : "preview not found under intake-v6-svg-preview", "SVG preview present");

  // Try open inspect dialog if button exists
  const inspectBtn = page.getByRole("button", { name: /inspect|mărește|mareste|preview|detalii/i }).first();
  if (await inspectBtn.isVisible().catch(() => false)) {
    await inspectBtn.click().catch(() => {});
    await page.waitForTimeout(500);
    log.screenshots.push(await shot(page, dir, "05b-preview-inspect"));
    await page.keyboard.press("Escape").catch(() => {});
  }

  // Layers / components
  const layerTable = page.getByTestId("intake-v6-layer-table");
  if (await layerTable.isVisible().catch(() => false)) {
    await layerTable.scrollIntoViewIfNeeded();
  }
  log.screenshots.push(await shot(page, dir, "06-layers-detected"));
  const layersUi = await collectUiSnapshot(page);
  note("layers", `${layersUi.layerRows?.length || 0} layer rows`, null, { ui: layersUi });

  const assignment = page.getByTestId("intake-v6-svg-component-assignment");
  if (await assignment.isVisible().catch(() => false)) {
    await assignment.scrollIntoViewIfNeeded();
    log.screenshots.push(await shot(page, dir, "07-components-assignment"));
  } else {
    log.screenshots.push(await shot(page, dir, "07-components-area"));
  }

  // Blockers / warnings
  log.screenshots.push(await shot(page, dir, "08-blockers-warnings"));

  // Persist analysis wait
  let persisted = null;
  const persistStart = Date.now();
  while (Date.now() - persistStart < 60_000) {
    const snap = await getWorkspace(ws.id);
    if (snap?.payload?.svg_source || snap?.payload?.svg_analysis_json) {
      persisted = snap;
      break;
    }
    await page.waitForTimeout(1000);
  }
  note(
    "analysis_persist_wait",
    persisted ? "analysis/svg present on workspace" : "no svg_source/analysis within 60s",
    "debounced persist of client analysis",
  );

  // Confirm roles if available (operator configuration path)
  const confirmAll = page.getByTestId("intake-v6-confirm-all-roles");
  if (await confirmAll.isVisible().catch(() => false)) {
    await confirmAll.click().catch(() => {});
    await page.waitForTimeout(1500);
    note("confirm_roles", "clicked confirm-all-roles");
  } else {
    note("confirm_roles", "confirm-all-roles not visible");
  }
  log.screenshots.push(await shot(page, dir, "09-after-role-confirm"));

  // Advance toward review / configuration if possible
  const footerNext = page.getByTestId("intake-v6-footer-next");
  if (await footerNext.isEnabled().catch(() => false)) {
    const label = ((await footerNext.textContent()) || "").trim();
    await footerNext.click().catch(() => {});
    await page.waitForTimeout(2000);
    note("advance_next", `clicked footer next: ${label}`);
  } else {
    note("advance_next", "footer next disabled or missing");
  }
  log.screenshots.push(await shot(page, dir, "10-after-advance"));

  // Review / product definition surface
  const reviewTab = page.getByTestId("intake-v6-progress-step-review");
  if (await reviewTab.isEnabled().catch(() => false)) {
    await reviewTab.click().catch(() => {});
    await page.waitForTimeout(1500);
  }
  const reviewUi = await collectUiSnapshot(page);
  log.screenshots.push(await shot(page, dir, "11-review-config"));
  note("review_config", reviewUi.stepReview ? "on review step" : "not on review step", null, { ui: reviewUi });

  // Letter groups / montaj tabs if present
  for (const tab of ["litere", "montaj", "finisaje", "electric"]) {
    const t = page.getByTestId(`intake-v6-review-tab-${tab}`);
    if (await t.isVisible().catch(() => false)) {
      await t.click().catch(() => {});
      await page.waitForTimeout(600);
      log.screenshots.push(await shot(page, dir, `11b-review-tab-${tab}`));
    }
  }

  // Workspace payload after config
  const afterConfigWs = await getWorkspace(ws.id);
  const afterConfigSummary = await summarizeWorkspacePayload(afterConfigWs);
  writeJson(path.join(dir, "workspace-after-config.json"), afterConfigSummary);
  writeJson(path.join(dir, "workspace-after-config-full.json"), {
    id: afterConfigWs.id,
    workspace_code: afterConfigWs.workspace_code,
    status: afterConfigWs.status,
    readiness_status: afterConfigWs.readiness_status,
    payload_keys: Object.keys(afterConfigWs.payload || {}),
    summary: afterConfigSummary,
  });

  // Soft "save" — trigger any save button if present
  const saveBtn = page.getByRole("button", { name: /salveaz|save|persist/i }).first();
  if (await saveBtn.isVisible().catch(() => false)) {
    await saveBtn.click().catch(() => {});
    await page.waitForTimeout(1500);
    note("save", "clicked save-like button");
  } else {
    note("save", "no explicit save button; relying on auto-persist");
  }
  log.screenshots.push(await shot(page, dir, "12-saved-state"));

  // Refresh + reopen
  await page.reload({ waitUntil: "domcontentloaded", timeout: 120_000 });
  await waitAuth(page);
  await page.getByTestId("intake-v6-header").waitFor({ state: "visible", timeout: 90_000 }).catch(() => {});
  await page.waitForTimeout(2000);
  log.screenshots.push(await shot(page, dir, "13-after-refresh"));
  const refreshUi = await collectUiSnapshot(page);
  const afterRefreshWs = await getWorkspace(ws.id);
  const afterRefreshSummary = await summarizeWorkspacePayload(afterRefreshWs);
  writeJson(path.join(dir, "workspace-after-refresh.json"), afterRefreshSummary);
  note(
    "refresh_persistence",
    {
      fileChip: refreshUi.fileChip,
      layerRows: refreshUi.layerRows?.length || 0,
      has_svg_source: afterRefreshSummary.has_svg_source,
      has_svg_analysis: afterRefreshSummary.has_svg_analysis,
      file_name: afterRefreshSummary.file_name,
    },
    "file + analysis + layers persist after refresh",
    { ui: refreshUi },
  );

  // Full page final
  log.screenshots.push(await shot(page, dir, "14-final", { fullPage: true }));
  log.screenshots.push(await shot(page, dir, "14-final-viewport"));

  log.consoleErrors = consoleErrors.slice(0, 40);
  log.finishedAt = new Date().toISOString();
  writeJson(path.join(dir, "runtime-log.json"), log);

  await context.close();
  return log;
}

async function main() {
  ensureDir(OUT);
  for (const c of CASES) {
    if (!fs.existsSync(c.file)) {
      throw new Error(`Required SVG missing: ${c.file}`);
    }
  }

  const browser = await chromium.launch({ headless: true });
  const results = [];
  for (const c of CASES) {
    console.log("=== RUN", c.id, c.file);
    try {
      const log = await runCase(browser, c);
      results.push({ id: c.id, ok: true, workspaceId: log.workspaceId, screenshots: log.screenshots.length });
      console.log("ok", c.id, "shots", log.screenshots.length);
    } catch (e) {
      console.error("FAIL", c.id, e);
      results.push({ id: c.id, ok: false, error: String(e) });
      writeJson(path.join(OUT, `${c.id}-FATAL.json`), { error: String(e), stack: e?.stack });
    }
  }
  await browser.close();
  writeJson(path.join(OUT, "capture-summary.json"), {
    at: new Date().toISOString(),
    viewport: VIEWPORT,
    backend: BACKEND,
    ui: UI,
    results,
  });
  console.log("DONE", JSON.stringify(results, null, 2));
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
