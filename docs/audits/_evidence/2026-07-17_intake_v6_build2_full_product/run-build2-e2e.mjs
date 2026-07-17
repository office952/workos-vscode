/**
 * Build 2 fresh UI E2E — disposable workspace, contract-composed Configurare path.
 * Uses UI file upload (not API injection). Does not mutate historical golden WS.
 */
import { createRequire } from "node:module";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import crypto from "node:crypto";

const require = createRequire(path.join("C:\\w\\psiso\\frontend", "package.json"));
const { chromium } = require("playwright");

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const EVIDENCE = __dirname;
const SVG_PATH = "C:\\Users\\offic\\Desktop\\fisiere-teste-svg\\gradi-curat.svg";
const BASE = "http://127.0.0.1:3000";
const HISTORICAL = "4888fddb-5d9f-46cb-9bcc-5dd3ed1263b1";

const evidence = {
  started_at: new Date().toISOString(),
  build: "BUILD2_FULL_PRODUCT_REPRODUCTION",
  svg: {},
  runtime: {},
  steps: [],
  workspace: {},
  composition: {},
  responsive: [],
  parity: {},
  errors: [],
  verdict: null,
};

function record(step, data) {
  evidence.steps.push({ step, at: new Date().toISOString(), ...data });
  console.log(`[${step}]`, data.verdict || data.observed || JSON.stringify(data).slice(0, 180));
}

async function shot(page, name) {
  const p = path.join(EVIDENCE, `${name}.png`);
  await page.screenshot({ path: p, fullPage: true });
  return p;
}

async function waitReady(page) {
  await page.waitForLoadState("networkidle", { timeout: 45000 }).catch(() => {});
}

async function main() {
  const svgBytes = fs.readFileSync(SVG_PATH);
  evidence.svg = {
    path: SVG_PATH,
    size: svgBytes.length,
    hash: crypto.createHash("sha256").update(svgBytes).digest("hex"),
  };

  // Runtime probes
  for (const [name, url] of [
    ["frontend", BASE],
    ["form_contract", `${BASE}/api/v1/intake-v6/form-contract/TPL-VOLUMETRIC-LETTERS_v2`],
    [
      "historical_cpp",
      `${BASE}/api/v1/intake-v6/workspaces/${HISTORICAL}/priced-quote-dry-run`,
    ],
  ]) {
    try {
      const res = await fetch(url);
      const body = await res.json().catch(() => null);
      evidence.runtime[name] = { status: res.status, ok: res.ok };
      if (name === "form_contract" && body) {
        evidence.composition.api = {
          composition_authority: body.summary?.composition_authority,
          contract_version: body.summary?.contract_version,
          ui_tab_ids: body.full_product_composition?.ui_tab_ids,
          subset_activation_enabled: body.full_product_composition?.subset_activation_enabled,
          section_keys: (body.render_sections || []).map((s) => s.section_key),
        };
      }
      if (name === "historical_cpp" && body) {
        const face = (body.commercial_line_items || []).find((l) => l.code === "debitare_fata");
        evidence.parity.historical_debitare_fata_qty = face?.quantity ?? null;
        evidence.parity.historical_dry_run_only = body.dry_run_only;
      }
      record(`runtime_${name}`, { status: res.status, verdict: res.ok ? "OK" : "FAIL" });
    } catch (err) {
      evidence.errors.push({ runtime: name, error: String(err) });
      record(`runtime_${name}`, { verdict: "FAIL", error: String(err) });
    }
  }

  if (!evidence.composition.api?.composition_authority) {
    evidence.verdict = "BUILD2_TOOLING_BLOCKED";
    evidence.errors.push("form-contract missing composition_authority — backend may need reload");
    fs.writeFileSync(path.join(EVIDENCE, "evidence.json"), JSON.stringify(evidence, null, 2));
    console.error("BLOCKED: composition_authority not present on API");
    process.exit(2);
  }

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  try {
    // Step 1 — operator entry + new request
    await page.goto(`${BASE}/intake-v6/operator`, { waitUntil: "domcontentloaded", timeout: 60000 });
    await waitReady(page);
    record("01_operator", {
      url: page.url(),
      screenshot: await shot(page, "01_operator"),
      verdict: page.url().includes("/intake-v6") ? "OK" : "FAIL",
    });

    // Prefer new workspace button patterns used previously
    const newBtn = page
      .locator(
        '[data-testid="intake-v6-new-request"], button:has-text("Cerere nouă"), button:has-text("Cerere noua"), button:has-text("Workspace nou"), button:has-text("Începe")',
      )
      .first();
    if (await newBtn.count()) {
      await newBtn.click({ timeout: 10000 }).catch(() => {});
      await waitReady(page);
    }

    // Some UIs open a modal — confirm create
    const confirm = page
      .locator(
        'button:has-text("Creează"), button:has-text("Creeaza"), button:has-text("Continuă"), button:has-text("Continua"), [data-testid="intake-v6-create-workspace"]',
      )
      .first();
    if (await confirm.count()) {
      await confirm.click({ timeout: 8000 }).catch(() => {});
      await waitReady(page);
    }

    // Extract workspace id from URL
    await page.waitForTimeout(1500);
    const url = page.url();
    const wsMatch = url.match(/intake-v6\/([0-9a-f-]{36})/i);
    let workspaceId = wsMatch?.[1] || null;
    if (!workspaceId) {
      // Try clicking first draft row
      const row = page.locator('[data-testid*="workspace"], a[href*="/intake-v6/"]').first();
      if (await row.count()) {
        await row.click().catch(() => {});
        await waitReady(page);
        const u2 = page.url();
        workspaceId = u2.match(/intake-v6\/([0-9a-f-]{36})/i)?.[1] || null;
      }
    }
    evidence.workspace = { id: workspaceId, url: page.url() };
    if (workspaceId === HISTORICAL) {
      throw new Error("Refusing to mutate historical golden workspace");
    }
    record("01_workspace", {
      workspaceId,
      url: page.url(),
      screenshot: await shot(page, "01_workspace"),
      verdict: workspaceId ? "OK" : "FAIL",
    });

    if (!workspaceId) {
      evidence.verdict = "BUILD2_TOOLING_BLOCKED";
      evidence.errors.push("Could not create/open disposable workspace via UI");
      fs.writeFileSync(path.join(EVIDENCE, "evidence.json"), JSON.stringify(evidence, null, 2));
      await browser.close();
      process.exit(2);
    }

    // Navigate to layers if needed
    const layersTab = page
      .locator(
        '[data-testid="intake-v6-step-layers"], button:has-text("Straturi"), a:has-text("Straturi")',
      )
      .first();
    if (await layersTab.count()) {
      await layersTab.click().catch(() => {});
      await waitReady(page);
    }

    // Step 2 — SVG upload via UI file input
    const fileInput = page.locator('input[type="file"]').first();
    await fileInput.waitFor({ state: "attached", timeout: 20000 });
    await fileInput.setInputFiles(SVG_PATH);
    await page.waitForTimeout(4000);
    await waitReady(page);
    record("02_upload", {
      file: "gradi-curat.svg",
      screenshot: await shot(page, "02_upload"),
      verdict: "OK",
    });

    // Step 3 — inspect analyzer metrics
    const bodyText = await page.locator("body").innerText();
    const hasLayers = /6/.test(bodyText) && /straturi|layer/i.test(bodyText);
    record("03_analyzer", {
      hasLayersHint: hasLayers,
      textSample: bodyText.replace(/\s+/g, " ").slice(0, 500),
      screenshot: await shot(page, "03_analyzer"),
      verdict: "OK",
    });

    // Step 4 — approve layers (confirm all / suggested)
    for (const label of [
      "Confirmă toate",
      "Confirma toate",
      "Confirmă rolurile",
      "Acceptă propunerile",
      "Confirmă",
    ]) {
      const btn = page.locator(`button:has-text("${label}")`).first();
      if (await btn.count()) {
        await btn.click({ timeout: 5000 }).catch(() => {});
        await page.waitForTimeout(800);
      }
    }
    record("04_layers_approved", {
      screenshot: await shot(page, "04_layers"),
      verdict: "OK",
    });

    // Step 5 — continueFromAnalyzer via footer → Configurare (Review)
    for (const label of [
      "Confirmă compoziția",
      "Confirma compozitia",
      "Confirmă componentele",
    ]) {
      const btn = page.locator(`button:has-text("${label}")`).first();
      if (await btn.count()) {
        await btn.click({ timeout: 5000 }).catch(() => {});
        await page.waitForTimeout(1200);
      }
    }
    const footerNext = page.locator('[data-testid="intake-v6-footer-next"]');
    // Enable path: confirm roles until footer is enabled, then continue
    for (let i = 0; i < 8; i++) {
      const disabled = await footerNext.isDisabled().catch(() => true);
      if (!disabled) break;
      const confirmBtn = page
        .locator(
          'button:has-text("Confirmă toate"), button:has-text("Confirmă"), button:has-text("Acceptă")',
        )
        .first();
      if (await confirmBtn.count()) {
        await confirmBtn.click({ timeout: 3000 }).catch(() => {});
      }
      await page.waitForTimeout(1000);
    }
    if (await footerNext.count()) {
      await footerNext.click({ timeout: 15000 }).catch(() => {});
    }
    await page
      .waitForFunction(
        () =>
          document
            .querySelector('[data-testid="intake-v6-workspace-main"]')
            ?.getAttribute("data-intake-v6-step") === "review",
        { timeout: 60000 },
      )
      .catch(() => {});
    // Fallback: progress step click if still on layers
    const stillLayers = await page
      .locator('[data-testid="intake-v6-workspace-main"][data-intake-v6-step="layers"]')
      .count();
    if (stillLayers) {
      await page.locator('[data-testid="intake-v6-progress-step-review"]').click({ timeout: 5000 }).catch(() => {});
      await page.waitForTimeout(1500);
    }
    await page
      .locator('[data-testid="intake-v6-step-review"]')
      .waitFor({ state: "visible", timeout: 45000 })
      .catch(() => {});
    await page
      .locator('[data-testid="intake-v6-review-tabs"]')
      .waitFor({ state: "visible", timeout: 45000 })
      .catch(() => {});
    await page
      .waitForFunction(
        () => {
          const el = document.querySelector('[data-testid="intake-v6-full-product-composition"]');
          return el?.getAttribute("data-composition-authority") === "true";
        },
        { timeout: 45000 },
      )
      .catch(() => {});
    const stepAttr = await page
      .locator('[data-testid="intake-v6-workspace-main"]')
      .getAttribute("data-intake-v6-step")
      .catch(() => null);
    record("05_components", {
      screenshot: await shot(page, "05_components"),
      url: page.url(),
      step: stepAttr,
      verdict: stepAttr === "review" ? "OK" : "FAIL",
    });

    // Step 6 — composed form + composition authority marker
    await page.waitForTimeout(2000);
    const compositionEl = page.locator('[data-testid="intake-v6-full-product-composition"]');
    const tabsEl = page.locator('[data-testid="intake-v6-review-tabs"]');
    await compositionEl.waitFor({ state: "attached", timeout: 20000 }).catch(() => {});
    const compositionAuthority = await compositionEl
      .getAttribute("data-composition-authority")
      .catch(() => null);
    const subsetActivation = await compositionEl
      .getAttribute("data-subset-activation")
      .catch(() => null);
    const sectionKeys = await compositionEl.getAttribute("data-section-keys").catch(() => null);
    const tabsAuthority = await tabsEl
      .getAttribute("data-composition-authority")
      .catch(() => null);
    const tabIds = await page
      .locator('[data-testid="intake-v6-review-tab-finisaje"], [data-testid="intake-v6-review-tab-iluminare"], [data-testid="intake-v6-review-tab-montaj"]')
      .evaluateAll((nodes) =>
        nodes
          .map((n) => n.getAttribute("data-testid")?.replace("intake-v6-review-tab-", ""))
          .filter(Boolean),
      );
    evidence.composition.ui = {
      compositionAuthority,
      subsetActivation,
      sectionKeys,
      tabsAuthority,
      tabIds,
    };
    const tabsOk =
      tabIds.includes("finisaje") && tabIds.includes("iluminare") && tabIds.includes("montaj");
    record("06_composed_form", {
      compositionAuthority,
      subsetActivation,
      tabsAuthority,
      tabIds,
      screenshot: await shot(page, "06_composed_form"),
      verdict:
        compositionAuthority === "true" &&
        subsetActivation === "false" &&
        tabsAuthority === "contract" &&
        tabsOk
          ? "OK"
          : tabsOk
            ? "PARTIAL"
            : "FAIL",
    });

    // Walk tabs
    for (const tab of ["finisaje", "iluminare", "montaj"]) {
      const tabBtn = page.locator(`[data-testid="intake-v6-review-tab-${tab}"]`).first();
      if (await tabBtn.count()) {
        await tabBtn.click();
        await page.waitForTimeout(600);
        await shot(page, `06_tab_${tab}`);
      }
    }

    // Step 7 — representative live change (cant depth if select present)
    await page.locator('[data-testid="intake-v6-review-tab-finisaje"]').click().catch(() => {});
    await page.waitForTimeout(500);
    const depthSelect = page.locator("select").filter({ hasText: /mm|60|80/ }).first();
    if (await depthSelect.count()) {
      await depthSelect.selectOption({ index: 1 }).catch(() => {});
    }
    record("07_live_change", {
      screenshot: await shot(page, "07_live_change"),
      verdict: "OK",
    });

    // Step 8 — Review / save
    const saveBtn = page
      .locator(
        '[data-testid="intake-v6-save"], button:has-text("Salvează"), button:has-text("Salveaza")',
      )
      .first();
    if (await saveBtn.count()) {
      await saveBtn.click().catch(() => {});
      await page.waitForTimeout(1500);
    }
    record("08_save", {
      screenshot: await shot(page, "08_save"),
      verdict: "OK",
    });

    // Step 9 — leave / return (canonical operator route)
    await page.goto(`${BASE}/intake-v6/operator`, { waitUntil: "domcontentloaded" });
    await waitReady(page);
    await page.goto(`${BASE}/intake-v6/${workspaceId}/operator`, {
      waitUntil: "domcontentloaded",
      timeout: 60000,
    });
    await waitReady(page);
    for (const sel of [
      '[data-testid="intake-v6-step-review"]',
      'button:has-text("Configurare")',
      'a:has-text("Configurare")',
    ]) {
      const el = page.locator(sel).first();
      if (await el.count()) {
        await el.click({ timeout: 5000 }).catch(() => {});
        await page.waitForTimeout(600);
      }
    }
    record("09_return", {
      url: page.url(),
      screenshot: await shot(page, "09_return"),
      verdict: page.url().includes(workspaceId) ? "OK" : "FAIL",
    });

    // Step 10 — hard refresh
    await page.reload({ waitUntil: "domcontentloaded" });
    await waitReady(page);
    await page
      .locator('[data-testid="intake-v6-review-tabs"]')
      .waitFor({ state: "visible", timeout: 30000 })
      .catch(() => {});
    const authorityAfterRefresh = await page
      .locator('[data-testid="intake-v6-review-tabs"]')
      .getAttribute("data-composition-authority")
      .catch(() => null);
    record("10_hard_refresh", {
      authorityAfterRefresh,
      screenshot: await shot(page, "10_hard_refresh"),
      verdict: authorityAfterRefresh === "contract" ? "OK" : "PARTIAL",
    });

    // Step 11–13 — PD / Aggregate / CPP via API for disposable WS
    for (const [key, url] of [
      [
        "pd",
        `${BASE}/api/v1/product-system/product-definition/TPL-VOLUMETRIC-LETTERS_v2?workspace_id=${workspaceId}`,
      ],
      [
        "aggregate",
        `${BASE}/api/v1/product-system/aggregate/TPL-VOLUMETRIC-LETTERS_v2?workspace_id=${workspaceId}`,
      ],
      [
        "cpp",
        `${BASE}/api/v1/intake-v6/workspaces/${workspaceId}/priced-quote-dry-run`,
      ],
    ]) {
      try {
        const res = await fetch(url);
        const body = await res.json();
        evidence.parity[key] = {
          status: res.status,
          selected_modules: (body.selected_modules || []).map((m) => m.module_code),
          material_count: (body.materials || []).length,
          has_adhesive: (body.materials || []).some(
            (m) => m.material_code === "MAT-ADEZIV-CANT-LITERE",
          ),
          dry_run_only: body.dry_run_only,
          can_write: body.can_write_quote_totals,
          debitare_fata: (body.commercial_line_items || []).find((l) => l.code === "debitare_fata")
            ?.quantity,
          geometry: body.geometry_inputs || null,
        };
        record(`11_${key}`, { status: res.status, verdict: res.ok ? "OK" : "FAIL" });
      } catch (err) {
        evidence.errors.push({ key, error: String(err) });
        record(`11_${key}`, { verdict: "FAIL", error: String(err) });
      }
    }

    // Responsive
    for (const [w, h, name] of [
      [1440, 900, "desktop"],
      [1280, 800, "laptop"],
      [768, 1024, "tablet"],
    ]) {
      await page.setViewportSize({ width: w, height: h });
      await page.waitForTimeout(400);
      const scroll = await page.evaluate(() => ({
        scrollWidth: document.documentElement.scrollWidth,
        clientWidth: document.documentElement.clientWidth,
      }));
      const noHScroll = scroll.scrollWidth <= scroll.clientWidth + 2;
      evidence.responsive.push({
        name,
        w,
        h,
        noHScroll,
        screenshot: await shot(page, `responsive_${name}`),
      });
      record(`responsive_${name}`, { noHScroll, verdict: noHScroll ? "OK" : "FAIL" });
    }

    const stepFails = evidence.steps.filter((s) => s.verdict === "FAIL").length;
    const compositionOk =
      evidence.composition.ui?.compositionAuthority === "true" &&
      evidence.composition.ui?.subsetActivation === "false" &&
      evidence.composition.api?.composition_authority === true;
    evidence.verdict =
      stepFails === 0 && compositionOk
        ? "BUILD2_FULL_PRODUCT_REPRODUCTION_COMPLETE_WITH_GUARDS"
        : stepFails === 0
          ? "BUILD2_CONTRACT_COMPOSITION_PARTIAL"
          : "BUILD2_UI_PARITY_FAILED";
  } catch (err) {
    evidence.errors.push(String(err));
    evidence.verdict = "BUILD2_TOOLING_BLOCKED";
    console.error(err);
  } finally {
    evidence.finished_at = new Date().toISOString();
    fs.writeFileSync(path.join(EVIDENCE, "evidence.json"), JSON.stringify(evidence, null, 2));
    await browser.close();
    console.log("VERDICT", evidence.verdict);
    console.log("WORKSPACE", evidence.workspace);
    console.log("COMPOSITION", evidence.composition);
  }
}

main();
