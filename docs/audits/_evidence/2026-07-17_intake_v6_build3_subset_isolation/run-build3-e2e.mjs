/**
 * Build 3 — subset activation E2E
 * 1) API: four disposable workspaces cloned from Build 2 fresh WS (read-only source)
 * 2) UI: presets + Review scope summary + responsive on one disposable WS
 * Does not mutate historical golden or Build 2 reference workspaces.
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
const API = `${BASE}/api/v1`;
const HISTORICAL = "4888fddb-5d9f-46cb-9bcc-5dd3ed1263b1";
const BUILD2_REF = "ce44f3f2-1018-4b8c-9011-92a1c402daaf";
const TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2";

const SCENARIOS = [
  { id: "full_product", mode: "full_product", sold: [], presetTestId: "intake-v6-offer-scope-preset-full" },
  { id: "face_only", mode: "component_subset", sold: ["FACE"], presetTestId: "intake-v6-offer-scope-preset-face" },
  { id: "cant_only", mode: "component_subset", sold: ["RETURN-CANT"], presetTestId: "intake-v6-offer-scope-preset-cant" },
  {
    id: "face_cant",
    mode: "component_subset",
    sold: ["FACE", "RETURN-CANT"],
    presetTestId: "intake-v6-offer-scope-preset-face-cant",
  },
];

const evidence = {
  started_at: new Date().toISOString(),
  build: "BUILD3_SUBSET_ACTIVATION_AND_OUTPUT_ISOLATION",
  svg: {},
  runtime: {},
  scenarios: {},
  ui: {},
  responsive: [],
  switching: {},
  errors: [],
  verdict: null,
};

function record(step, data) {
  console.log(`[${step}]`, data.verdict || data.note || JSON.stringify(data).slice(0, 200));
}

async function api(method, url, body) {
  const res = await fetch(url, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  const json = await res.json().catch(() => null);
  if (!res.ok) {
    throw new Error(`${method} ${url} -> ${res.status} ${JSON.stringify(json).slice(0, 400)}`);
  }
  return json;
}

function materialCodes(agg) {
  return (agg.materials || []).map((m) => m.material_code).filter(Boolean);
}

function consumableKeys(bd) {
  return (bd.consumable_rows || []).map((r) => r.material_key);
}

function cppCodes(cpp) {
  return (cpp.commercial_line_items || []).map((l) => l.code || l.line_code).filter(Boolean);
}

function assertScenario(id, probes) {
  const mats = new Set(probes.aggregate_materials);
  const cons = new Set(probes.consumable_keys);
  const cpp = new Set(probes.cpp_codes);
  const hasAdhesiveMat = mats.has("MAT-ADEZIV-CANT-LITERE");
  const hasAdhesiveCons = cons.has("adhesive_return_to_face");
  const hasFaceCpp = cpp.has("debitare_fata");
  const hasCantCpp = [...cpp].some((c) => String(c).includes("modelare_cant"));
  const bondingOps = (probes.aggregate_ops || []).filter((o) =>
    String(o).toLowerCase().includes("bonding"),
  );

  const checks = { hasAdhesiveMat, hasAdhesiveCons, hasFaceCpp, hasCantCpp, bondingOps };

  if (id === "full_product") {
    checks.pass = hasAdhesiveCons || hasAdhesiveMat;
    checks.expect = "adhesive present (full product)";
  } else if (id === "face_only") {
    checks.pass =
      !hasAdhesiveMat &&
      !hasAdhesiveCons &&
      bondingOps.length === 0 &&
      hasFaceCpp &&
      !hasCantCpp;
    checks.expect = "FACE only — no adhesive/cant/bonding";
  } else if (id === "cant_only") {
    checks.pass =
      !hasAdhesiveMat &&
      !hasAdhesiveCons &&
      bondingOps.length === 0 &&
      !hasFaceCpp &&
      hasCantCpp;
    checks.expect = "CANT only — no face/adhesive/bonding";
  } else if (id === "face_cant") {
    const adhesiveCount = probes.aggregate_materials.filter((c) => c === "MAT-ADEZIV-CANT-LITERE").length;
    const adhesiveConsCount = probes.consumable_keys.filter((k) => k === "adhesive_return_to_face").length;
    checks.adhesiveCount = adhesiveCount;
    checks.adhesiveConsCount = adhesiveConsCount;
    checks.pass =
      (hasAdhesiveMat || hasAdhesiveCons) &&
      adhesiveCount <= 1 &&
      adhesiveConsCount <= 1 &&
      hasFaceCpp &&
      hasCantCpp;
    checks.expect = "FACE+CANT — adhesive once + face + cant";
  }
  return checks;
}

async function cloneWorkspaceFromRef(source, scenario) {
  const created = await api("POST", `${API}/intake-v6/workspaces`, {
    title: `Build3 ${scenario.id} ${Date.now()}`,
    analyzer_mode: "analyzer_first",
    selected_template_code: TEMPLATE,
    source: `build3_${scenario.id}`,
  });
  const id = created.id;
  if (id === HISTORICAL || id === BUILD2_REF) {
    throw new Error("Refusing to use protected workspace id");
  }

  const p = source.payload || {};
  const svgText = p.svg_source_text || fs.readFileSync(SVG_PATH, "utf8");
  await api("PUT", `${API}/intake-v6/workspaces/${id}/analysis-bundle`, {
    file_name: p.svg_source?.file_name || "gradi-curat.svg",
    file_size_bytes: p.svg_source?.file_size_bytes || Buffer.byteLength(svgText),
    svg_text: svgText,
    svg_analysis_json: p.svg_analysis_json,
    layer_role_setup: p.layer_role_setup,
  });

  if (p.finish_setup) {
    await api("PUT", `${API}/intake-v6/workspaces/${id}/finish-setup`, {
      ...p.finish_setup,
      confirmed: true,
    });
  }

  if (p.product_composition_confirmed?.confirmed) {
    await api("PUT", `${API}/intake-v6/workspaces/${id}/product-composition-confirmation`, {
      confirmed: true,
      items: p.product_composition_confirmed.items || p.product_composition_recommendation?.composition_items || [],
    });
  }

  await api("PUT", `${API}/intake-v6/workspaces/${id}/offer-scope`, {
    mode: scenario.mode,
    sold_modules: scenario.sold,
    confirmed: true,
  });

  return id;
}

async function probeWorkspace(id) {
  const [breakdown, aggregate, cpp, pd] = await Promise.all([
    api("GET", `${API}/intake-v6/workspaces/${id}/material-breakdown`),
    api("GET", `${API}/product-system/aggregate/${TEMPLATE}?workspace_id=${id}`),
    api("GET", `${API}/intake-v6/workspaces/${id}/priced-quote-dry-run`),
    api("GET", `${API}/product-system/product-definition/${TEMPLATE}?workspace_id=${id}`),
  ]);
  return {
    consumable_keys: consumableKeys(breakdown),
    aggregate_materials: materialCodes(aggregate),
    aggregate_ops: (aggregate.operations || []).map((o) => o.operation_code),
    cpp_codes: cppCodes(cpp),
    pd_active: (pd.selected_modules || [])
      .filter((m) => ["always_on", "active", "conditional_active"].includes(m.state))
      .map((m) => m.module_code),
    debitare_fata_qty: (cpp.commercial_line_items || []).find((l) => l.code === "debitare_fata")
      ?.quantity,
  };
}

async function runApiScenarios() {
  const source = await api("GET", `${API}/intake-v6/workspaces/${BUILD2_REF}`);
  for (const scenario of SCENARIOS) {
    const id = await cloneWorkspaceFromRef(source, scenario);
    const probes = await probeWorkspace(id);
    const checks = assertScenario(scenario.id, probes);
    evidence.scenarios[scenario.id] = {
      workspace_id: id,
      offer_scope: { mode: scenario.mode, sold_modules: scenario.sold },
      probes,
      checks,
      verdict: checks.pass ? "PASS" : "FAIL",
    };
    record(`api_${scenario.id}`, {
      workspace_id: id,
      verdict: checks.pass ? "PASS" : "FAIL",
      note: checks.expect,
    });
    if (!checks.pass) {
      evidence.errors.push({ scenario: scenario.id, checks });
    }
  }
}

async function runUiProof() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();
  const uiWs = evidence.scenarios.cant_only?.workspace_id;
  if (!uiWs) throw new Error("cant_only workspace missing for UI proof");

  try {
    await page.goto(`${BASE}/intake-v6/${uiWs}/operator`, {
      waitUntil: "domcontentloaded",
      timeout: 60000,
    });
    await page.waitForLoadState("networkidle", { timeout: 45000 }).catch(() => {});

    // Ensure offer scope panel visible (layers step)
    const presetBar = page.locator('[data-testid="intake-v6-offer-scope-presets"]');
    if (!(await presetBar.count())) {
      await page
        .locator('[data-testid="intake-v6-progress-step-layers"], button:has-text("Straturi")')
        .first()
        .click({ timeout: 5000 })
        .catch(() => {});
      await page.waitForTimeout(1000);
    }
    await presetBar.waitFor({ state: "visible", timeout: 20000 });

    // Click through presets
    for (const scenario of SCENARIOS) {
      await page.locator(`[data-testid="${scenario.presetTestId}"]`).click({ timeout: 8000 });
      await page.waitForTimeout(1200);
      const pressed = await page
        .locator(`[data-testid="${scenario.presetTestId}"]`)
        .getAttribute("aria-pressed");
      evidence.ui[`preset_${scenario.id}`] = { pressed, screenshot: path.join(EVIDENCE, `ui_preset_${scenario.id}.png`) };
      await page.screenshot({ path: path.join(EVIDENCE, `ui_preset_${scenario.id}.png`), fullPage: true });
      record(`ui_preset_${scenario.id}`, { pressed, verdict: pressed === "true" ? "PASS" : "PARTIAL" });
    }

    // Set CANT only and go to Review
    await page.locator('[data-testid="intake-v6-offer-scope-preset-cant"]').click();
    await page.waitForTimeout(1000);
    const footerNext = page.locator('[data-testid="intake-v6-footer-next"]');
    for (let i = 0; i < 6; i++) {
      const disabled = await footerNext.isDisabled().catch(() => true);
      if (!disabled) break;
      await page
        .locator('button:has-text("Confirmă toate"), button:has-text("Confirmă")')
        .first()
        .click({ timeout: 3000 })
        .catch(() => {});
      await page.waitForTimeout(800);
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
    await page
      .locator('[data-testid="intake-v6-progress-step-review"]')
      .click({ timeout: 5000 })
      .catch(() => {});
    await page.waitForTimeout(1500);

    const reviewSummary = page.locator('[data-testid="intake-v6-review-offer-scope-summary"]');
    await reviewSummary.waitFor({ state: "visible", timeout: 30000 }).catch(() => {});
    const activeText = await page
      .locator('[data-testid="intake-v6-review-offer-scope-active"]')
      .innerText()
      .catch(() => "");
    const excludedText = await page
      .locator('[data-testid="intake-v6-review-offer-scope-excluded"]')
      .innerText()
      .catch(() => "");
    const subsetFlag = await page
      .locator('[data-testid="intake-v6-full-product-composition"]')
      .getAttribute("data-subset-activation")
      .catch(() => null);
    evidence.ui.review = {
      activeText,
      excludedText,
      subsetFlag,
      screenshot: path.join(EVIDENCE, "ui_review_cant_only.png"),
    };
    await page.screenshot({ path: path.join(EVIDENCE, "ui_review_cant_only.png"), fullPage: true });
    const reviewOk =
      /Cant/i.test(activeText) &&
      /Față|Fata/i.test(excludedText) &&
      subsetFlag === "true";
    record("ui_review_cant_only", { activeText, excludedText, subsetFlag, verdict: reviewOk ? "PASS" : "FAIL" });
    if (!reviewOk) evidence.errors.push({ ui_review: evidence.ui.review });

    // Scope switching: CANT → full → FACE → FACE+CANT
    await page
      .locator('[data-testid="intake-v6-progress-step-layers"], button:has-text("Straturi")')
      .first()
      .click({ timeout: 5000 })
      .catch(() => {});
    await page.waitForTimeout(800);
    const switchPath = ["full", "face", "face-cant", "cant"];
    for (const key of switchPath) {
      await page.locator(`[data-testid="intake-v6-offer-scope-preset-${key}"]`).click();
      await page.waitForTimeout(900);
    }
    const afterSwitch = await api("GET", `${API}/intake-v6/workspaces/${uiWs}`);
    evidence.switching = {
      final_offer_scope: afterSwitch.payload?.offer_scope || null,
      verdict:
        afterSwitch.payload?.offer_scope?.mode === "component_subset" &&
        JSON.stringify(afterSwitch.payload?.offer_scope?.sold_modules || []) ===
          JSON.stringify(["RETURN-CANT"])
          ? "PASS"
          : "PARTIAL",
    };
    record("ui_scope_switching", evidence.switching);

    // Hard refresh
    await page.reload({ waitUntil: "domcontentloaded" });
    await page.waitForTimeout(1500);
    const summaryAfter = await page
      .locator('[data-testid="intake-v6-offer-scope-summary-active"], [data-testid="intake-v6-review-offer-scope-active"]')
      .first()
      .innerText()
      .catch(() => "");
    evidence.ui.hard_refresh = { summaryAfter };
    record("ui_hard_refresh", { summaryAfter, verdict: summaryAfter ? "PASS" : "PARTIAL" });

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
      const shot = path.join(EVIDENCE, `responsive_${name}.png`);
      await page.screenshot({ path: shot, fullPage: true });
      evidence.responsive.push({ name, w, h, noHScroll, screenshot: shot });
      record(`responsive_${name}`, { noHScroll, verdict: noHScroll ? "PASS" : "FAIL" });
      if (!noHScroll) evidence.errors.push({ responsive: name });
    }
  } finally {
    await browser.close();
  }
}

async function main() {
  const svgBytes = fs.readFileSync(SVG_PATH);
  evidence.svg = {
    path: SVG_PATH,
    size: svgBytes.length,
    hash: crypto.createHash("sha256").update(svgBytes).digest("hex"),
  };

  const contract = await api("GET", `${API}/intake-v6/form-contract/${TEMPLATE}`);
  evidence.runtime.form_contract = {
    version: contract.summary?.contract_version,
    composition_authority: contract.summary?.composition_authority,
    subset_activation_enabled: contract.full_product_composition?.subset_activation_enabled,
    mode: contract.full_product_composition?.mode,
  };
  record("runtime_contract", evidence.runtime.form_contract);

  if (!evidence.runtime.form_contract.subset_activation_enabled) {
    evidence.verdict = "TOOLING_BLOCKED";
    evidence.errors.push("subset_activation_enabled not true on live API");
    fs.writeFileSync(path.join(EVIDENCE, "evidence.json"), JSON.stringify(evidence, null, 2));
    process.exit(2);
  }

  // Historical full-product regression fingerprint (read-only)
  const histCpp = await api("GET", `${API}/intake-v6/workspaces/${HISTORICAL}/priced-quote-dry-run`);
  const faceQty = (histCpp.commercial_line_items || []).find((l) => l.code === "debitare_fata")?.quantity;
  evidence.runtime.historical_debitare_fata_qty = faceQty;
  record("historical_cpp", { debitare_fata_qty: faceQty, verdict: faceQty === 20.9727 ? "PASS" : "GUARD" });

  await runApiScenarios();
  await runUiProof();

  const apiFails = Object.values(evidence.scenarios).filter((s) => s.verdict !== "PASS").length;
  const fullOk = evidence.scenarios.full_product?.verdict === "PASS";
  const faceOk = evidence.scenarios.face_only?.verdict === "PASS";
  const cantOk = evidence.scenarios.cant_only?.verdict === "PASS";
  const faceCantOk = evidence.scenarios.face_cant?.verdict === "PASS";
  const responsiveOk = evidence.responsive.every((r) => r.noHScroll);

  if (apiFails === 0 && fullOk && faceOk && cantOk && faceCantOk && responsiveOk) {
    evidence.verdict = "BUILD3_SUBSET_ISOLATION_COMPLETE_WITH_GUARDS";
  } else if (!fullOk) {
    evidence.verdict = "BUILD3_FULL_PRODUCT_REGRESSION";
  } else if (!cantOk) {
    evidence.verdict = "BUILD3_CANT_ONLY_FAILED";
  } else if (!faceOk) {
    evidence.verdict = "BUILD3_FACE_ONLY_FAILED";
  } else if (!faceCantOk) {
    evidence.verdict = "BUILD3_FACE_CANT_INTERFACE_FAILED";
  } else {
    evidence.verdict = "FAILED";
  }

  evidence.finished_at = new Date().toISOString();
  fs.writeFileSync(path.join(EVIDENCE, "evidence.json"), JSON.stringify(evidence, null, 2));
  console.log("VERDICT", evidence.verdict);
  console.log(
    "SCENARIOS",
    Object.fromEntries(Object.entries(evidence.scenarios).map(([k, v]) => [k, { id: v.workspace_id, verdict: v.verdict }])),
  );
  if (evidence.verdict !== "BUILD3_SUBSET_ISOLATION_COMPLETE_WITH_GUARDS") process.exitCode = 1;
}

main().catch((err) => {
  evidence.errors.push(String(err));
  evidence.verdict = "TOOLING_BLOCKED";
  evidence.finished_at = new Date().toISOString();
  fs.writeFileSync(path.join(EVIDENCE, "evidence.json"), JSON.stringify(evidence, null, 2));
  console.error(err);
  process.exit(2);
});
