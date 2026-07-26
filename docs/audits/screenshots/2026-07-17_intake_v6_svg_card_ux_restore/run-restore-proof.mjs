/**
 * RESTORE_EXISTING_SVG_CARD_UX_WITH_ACP — runtime proof on existing workspace.
 */
import { createRequire } from "node:module";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(path.join("C:\\w\\psiso\\frontend", "package.json"));
const { chromium } = require("playwright");

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT = __dirname;
const SVG_PATH = "C:\\Users\\offic\\Desktop\\fisiere-teste-svg\\LITERE-VOLUMETRICE-ACP.svg";
const BASE = "http://127.0.0.1:3000";
const WS = "9c05851e-3230-4a97-821b-e52293ada844";

const report = {
  started_at: new Date().toISOString(),
  workspace_id: WS,
  checks: {},
  screenshots: [],
  errors: [],
  verdict: null,
};

async function shot(page, name) {
  const p = path.join(OUT, `${name}.png`);
  await page.screenshot({ path: p, fullPage: false });
  report.screenshots.push(p);
  return p;
}

async function goLayers(page) {
  for (let attempt = 0; attempt < 5; attempt++) {
    const step = await page
      .locator("[data-intake-v6-step]")
      .getAttribute("data-intake-v6-step")
      .catch(() => null);
    if (step === "layers" && (await page.locator('[data-testid="intake-v6-svg-analyzer-step"]').count())) {
      return;
    }
    await page.locator('[data-testid="intake-v6-progress-step-layers"]').click({ force: true });
    await page.waitForTimeout(900);
  }
  await page.locator('[data-testid="intake-v6-svg-analyzer-step"]').waitFor({
    state: "attached",
    timeout: 10000,
  });
}

async function main() {
  if (!fs.existsSync(SVG_PATH)) throw new Error(`Missing fixture: ${SVG_PATH}`);
  fs.mkdirSync(OUT, { recursive: true });

  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  page.setDefaultTimeout(45000);

  try {
    await page.goto(`${BASE}/intake-v6/${WS}/operator`, {
      waitUntil: "domcontentloaded",
      timeout: 60000,
    });
    await page.waitForLoadState("networkidle").catch(() => {});
    await page.waitForTimeout(2000);

    // Capture composition label from review if visible (proof of ACP in composition)
    const reviewSummary = await page
      .locator('[data-testid="intake-v6-product-composition-summary"]')
      .first()
      .textContent()
      .catch(() => null);
    if (reviewSummary) {
      report.checks.composition_summary_pre = reviewSummary.trim();
      report.checks.composition_includes_acp_pre = /Alucobond|ACP/i.test(reviewSummary);
    }

    await goLayers(page);

    // Upload ACP fixture via change-file path
    const changeBtn = page
      .locator('button:has-text("Schimbă fișier"), button:has-text("Schimba fisier")')
      .first();
    if (await changeBtn.count()) {
      await changeBtn.click().catch(() => {});
      await page.waitForTimeout(500);
    }
    const input = page
      .locator(
        '[data-testid="intake-v6-svg-input-change"], [data-testid="intake-v6-svg-input"], [data-testid="intake-v6-svg-input-preview"]',
      )
      .first();
    await input.waitFor({ state: "attached", timeout: 20000 });
    await input.setInputFiles(SVG_PATH);

    // Wait for local analyze + ACP card
    await page
      .locator('[data-testid="intake-v6-support-contour-card"]')
      .waitFor({ state: "attached", timeout: 30000 });
    await page.waitForTimeout(2500);
    await goLayers(page);

    // Allow autosave timer (~900ms) + network
    await page.waitForTimeout(3000);
    await page.waitForLoadState("networkidle").catch(() => {});
    await goLayers(page);

    const acpCard = page.locator('[data-testid="intake-v6-support-contour-card"]');
    await acpCard.waitFor({ state: "attached", timeout: 15000 });
    await acpCard.scrollIntoViewIfNeeded();
    await page.waitForTimeout(400);

    await shot(page, "01_page_after_acp_upload");
    await shot(page, "02_cards_grid_with_acp");

    const bodyText = await page.locator("body").innerText();
    report.checks.ui_shows_acp_filename = /LITERE-VOLUMETRICE-ACP\.svg/i.test(bodyText);
    report.checks.no_rezumat_asocieri = !/Rezumat asocieri/i.test(bodyText);
    report.checks.no_confirma_selectia = !/Confirmă selecția|Confirma selectia/i.test(bodyText);
    report.checks.no_standalone_contur_suport_panel =
      (await page.locator('[data-testid="intake-v6-alucobond-contour-panel"]').count()) === 0;
    report.checks.acp_card_present = (await acpCard.count()) > 0;
    report.checks.acp_card_title =
      (await page.locator('[data-testid="intake-v6-support-contour-card"]:has-text("Panou ACP")').count()) >
      0;
    report.checks.acp_card_in_grid =
      (await page
        .locator('[data-testid="intake-v6-layer-card-grid"] [data-testid="intake-v6-support-contour-card"]')
        .count()) > 0;

    const pickerVisible = await page
      .locator('[data-testid="intake-v6-support-geometry-picker"]')
      .isVisible()
      .catch(() => false);
    report.checks.no_permanent_candidate_list =
      !pickerVisible && (await page.locator('[data-testid="intake-v6-support-contour-card"] li').count()) === 0;

    report.checks.layer_cards_in_grid = await page
      .locator('[data-testid="intake-v6-layer-card-grid"] [data-testid^="intake-v6-layer-row-"]')
      .count();
    report.checks.assignment_panel_absent =
      (await page.locator('[data-testid="intake-v6-svg-component-assignment-panel"]').count()) === 0 &&
      !/Rezumat asocieri produs/i.test(bodyText);

    // Associate ACP
    const roleSelect = page.locator('[data-testid="intake-v6-support-geometry-role"]');
    const current = await roleSelect.inputValue().catch(() => "");
    if (current !== "SUPPORT_CONTOUR") {
      await roleSelect.selectOption("SUPPORT_CONTOUR");
      await page.waitForTimeout(2500);
      await page.waitForLoadState("networkidle").catch(() => {});
    }
    await goLayers(page);
    await acpCard.scrollIntoViewIfNeeded();
    await page.waitForTimeout(400);
    await shot(page, "03_acp_associated");

    const associatedSelect = await roleSelect.inputValue().catch(() => "");
    report.checks.acp_associated_ui = associatedSelect === "SUPPORT_CONTOUR";

    // Composition on layers step
    const summary = page.locator('[data-testid="intake-v6-product-composition-summary"]').first();
    await summary.scrollIntoViewIfNeeded().catch(() => {});
    await page.waitForTimeout(400);
    const summaryText = ((await summary.textContent().catch(() => null)) || "").trim();
    report.checks.composition_summary = summaryText || null;
    report.checks.composition_includes_acp_ui = /Alucobond|ACP/i.test(summaryText);
    await shot(page, "04_composition_after_acp");

    // API probe
    const apiRes = await fetch(`${BASE}/api/v1/intake-v6/workspaces/${WS}`);
    const apiJson = await apiRes.json().catch(() => null);
    const rec = apiJson?.payload?.product_composition_recommendation;
    report.checks.api_composition_type = rec?.composition_type ?? null;
    report.checks.api_composition_includes_support = String(rec?.composition_type || "").includes(
      "support",
    );
    const bindings = apiJson?.payload?.finish_setup?.svg_component_bindings;
    report.checks.api_has_support_binding =
      Array.isArray(bindings) &&
      bindings.some(
        (b) =>
          String(b.geometry_role || "") === "SUPPORT_CONTOUR" ||
          String(b.component_template_code || "").includes("ACM"),
      );
    report.checks.api_svg_file = apiJson?.payload?.svg_source?.file_name ?? null;

    // Detalii tehnice — no permanent list
    await acpCard.scrollIntoViewIfNeeded();
    const details = acpCard.locator("details summary");
    if (await details.count()) {
      await details.click().catch(() => {});
      await page.waitForTimeout(300);
    }
    report.checks.picker_still_closed_after_details = !(await page
      .locator('[data-testid="intake-v6-support-geometry-picker"]')
      .isVisible()
      .catch(() => false));
    await shot(page, "05_acp_details_no_candidate_list");

    report.checks.composition_includes_acp =
      report.checks.api_composition_includes_support === true ||
      report.checks.composition_includes_acp_ui === true ||
      report.checks.composition_includes_acp_pre === true;

    const requiredTrue = [
      "no_rezumat_asocieri",
      "no_confirma_selectia",
      "no_standalone_contur_suport_panel",
      "acp_card_present",
      "acp_card_title",
      "acp_card_in_grid",
      "no_permanent_candidate_list",
      "assignment_panel_absent",
      "acp_associated_ui",
      "composition_includes_acp",
      "api_has_support_binding",
      "picker_still_closed_after_details",
    ];
    const fails = requiredTrue.filter((k) => report.checks[k] !== true);
    if (typeof report.checks.layer_cards_in_grid !== "number" || report.checks.layer_cards_in_grid < 1) {
      fails.push("layer_cards_in_grid");
    }

    report.verdict =
      fails.length === 0
        ? "EXISTING_SVG_CARD_UX_RESTORED_WITH_ACP"
        : "EXISTING_CARD_MODEL_NEEDS_MINIMAL_EXTENSION";
    report.failing_checks = fails;
    report.finished_at = new Date().toISOString();

    fs.writeFileSync(path.join(OUT, "runtime-proof.json"), JSON.stringify(report, null, 2));
    console.log(JSON.stringify(report, null, 2));
    if (fails.length) process.exitCode = 2;
  } catch (err) {
    report.errors.push(String(err?.stack || err));
    report.verdict = "EXISTING_CARD_MODEL_NEEDS_MINIMAL_EXTENSION";
    fs.writeFileSync(path.join(OUT, "runtime-proof.json"), JSON.stringify(report, null, 2));
    console.error(err);
    process.exitCode = 1;
  } finally {
    await browser.close();
  }
}

main();
