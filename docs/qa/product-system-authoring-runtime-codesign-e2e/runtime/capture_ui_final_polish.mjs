/**
 * PRODUCT SYSTEM UI / FIGMA FINAL POLISH — screenshot pack 1–23.
 * Never invent Publication-ready for VolumetricLetters.
 */
import { createRequire } from "node:module";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(path.join("C:", "w", "psiso", "frontend", "package.json"));
const { chromium } = require("playwright");
const OUT = path.resolve(__dirname, "../screenshots");
const FE = process.env.FE_BASE || "http://127.0.0.1:3000";
const VL_CODE = "TPL-VOLUMETRIC-LETTERS_v2";
const VL = `${FE}/product-system/products/${VL_CODE}`;

fs.mkdirSync(OUT, { recursive: true });

const evidence = {
  fe: FE,
  captured_at: new Date().toISOString(),
  shots: [],
  console_errors: [],
  notes: [],
};

async function shot(page, name, note) {
  const dest = path.join(OUT, `${name}.png`);
  await page.screenshot({ path: dest, fullPage: true });
  const size = fs.statSync(dest).size;
  evidence.shots.push({ name, note, size, ok: size > 1000 });
  console.log(`OK ${name}.png (${size}) ${note}`);
}

async function clickTab(page, testId) {
  const tab = page.getByTestId(testId);
  if ((await tab.count()) === 0) {
    evidence.notes.push(`MISSING_TAB ${testId}`);
    return false;
  }
  await tab.first().click();
  await page.waitForTimeout(900);
  return true;
}

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
page.on("console", (msg) => {
  if (msg.type() === "error") evidence.console_errors.push(msg.text());
});
page.on("pageerror", (err) => evidence.console_errors.push(String(err)));

await page.goto(`${FE}/product-system/products`, { waitUntil: "domcontentloaded", timeout: 60000 });
await page.waitForTimeout(2500);
await shot(page, "polish_01_landing_products", "Landing /product-system/products");

await page.goto(VL, { waitUntil: "domcontentloaded", timeout: 60000 });
await page.waitForTimeout(3000);
await shot(page, "polish_02_template_overview_dual_chips", "Overview + dual status chips");

await clickTab(page, "product-system-template-detail-tab-composition");
await shot(page, "polish_03_composition_authoring", "Composition authoring");

await clickTab(page, "product-system-template-detail-tab-components");
await shot(page, "polish_04_components_list", "Components diagnostic list");

await clickTab(page, "product-system-template-detail-tab-contracts");
await shot(page, "polish_05_contracts_used_by", "Component contracts / used-by");

await clickTab(page, "product-system-template-detail-tab-relationships");
await shot(page, "polish_06_relationships", "Relationships map");

await clickTab(page, "product-system-template-detail-tab-materials");
await shot(page, "polish_07_materials_preview", "Materials via PD preview");

await clickTab(page, "product-system-template-detail-tab-dossier");
await shot(page, "polish_08_dossier_tab_cta", "Dossier tab + Studio CTA");

await page.goto(`${FE}/product-system/blueprint-dossier?template=${encodeURIComponent(VL_CODE)}`, {
  waitUntil: "domcontentloaded",
  timeout: 60000,
});
await page.waitForTimeout(3500);
await shot(page, "polish_09_dossier_studio_deeplink", "Dossier Studio deep-link ?template=");

const footer = page.getByTestId("blueprint-dossier-sticky-publish-footer");
if (await footer.count()) {
  await footer.first().scrollIntoViewIfNeeded();
  await page.waitForTimeout(300);
  await shot(page, "polish_10_sticky_save_validate_check_publish", "Sticky Salvează→Validează→Verifică→Publică");
} else {
  evidence.notes.push("MISSING sticky footer");
}

await page.goto(VL, { waitUntil: "domcontentloaded", timeout: 60000 });
await page.waitForTimeout(2500);
await clickTab(page, "product-system-template-detail-tab-runtime-preview");
await shot(page, "polish_11_runtime_preview_summary", "Runtime Preview human summary");

await clickTab(page, "product-system-template-detail-tab-readiness");
const readyBtn = page.getByTestId("product-e2e-readiness-static-btn");
if (await readyBtn.count()) {
  await readyBtn.first().click();
  await page.waitForTimeout(3000);
}
await shot(page, "polish_12_readiness_dual_axes", "Readiness BUILD vs TEMPLATE BLOCKED");

await clickTab(page, "product-system-template-detail-tab-publication");
await page.waitForTimeout(1500);
await shot(page, "polish_13_publication_blocked_human", "Publication blocked — human name primary");

await clickTab(page, "product-system-template-detail-tab-guards");
await shot(page, "polish_14_diagnostic_guards", "Diagnostic / guards (secondary)");

await page.goto(`${FE}/product-system/blueprint-dossier?template=${encodeURIComponent(VL_CODE)}`, {
  waitUntil: "domcontentloaded",
  timeout: 60000,
});
await page.waitForTimeout(2500);
const pubD = page.getByTestId("product-template-publication-panel");
if (await pubD.count()) {
  await pubD.first().scrollIntoViewIfNeeded();
  await shot(page, "polish_15_dossier_publication_blocked", "Dossier rail publication blocked");
}
const readyD = page.getByTestId("product-e2e-readiness-panel");
if (await readyD.count()) {
  await readyD.first().scrollIntoViewIfNeeded();
  const btn = page.getByTestId("product-e2e-readiness-static-btn");
  if (await btn.count()) {
    await btn.first().click();
    await page.waitForTimeout(2500);
  }
  await shot(page, "polish_16_dossier_readiness_compact", "Dossier readiness compact dual axes");
}

await page.goto(VL, { waitUntil: "domcontentloaded", timeout: 60000 });
await page.waitForTimeout(2000);
await clickTab(page, "product-system-template-detail-tab-overview");
await shot(page, "polish_17_overview_modularity_collapsed", "Overview — modularity progressive disclosure");

await clickTab(page, "product-system-template-detail-tab-composition");
await shot(page, "polish_18_composition_contract_details", "Composition with contract details collapsed");

await clickTab(page, "product-system-template-detail-tab-readiness");
await page.waitForTimeout(800);
const toggle = page.getByTestId("product-e2e-readiness-toggle");
if (await toggle.count()) {
  await toggle.first().click();
  await page.waitForTimeout(400);
}
await shot(page, "polish_19_readiness_expanded_actions", "Readiness expanded actions");

await clickTab(page, "product-system-template-detail-tab-runtime-preview");
await shot(page, "polish_20_runtime_diagnostics_collapsed", "Runtime diagnostics collapsed");

await page.goto(`${FE}/product-system/products`, { waitUntil: "domcontentloaded", timeout: 45000 });
await page.waitForTimeout(1500);
await shot(page, "polish_21_shell_nav_products", "Shell nav — Products active");

await page.goto(`${FE}/product-system/components`, { waitUntil: "domcontentloaded", timeout: 45000 });
await page.waitForTimeout(1200);
await shot(page, "polish_22_planned_section_honesty", "Planned Components section honesty");

await page.goto(VL, { waitUntil: "domcontentloaded", timeout: 60000 });
await page.waitForTimeout(2000);
await clickTab(page, "product-system-template-detail-tab-publication");
await page.waitForTimeout(1200);
const banner = page.getByTestId("product-template-publication-blocked-banner");
evidence.panels = {
  publication_blocked_banner: await banner.count(),
  dual_chips: await page.getByTestId("template-dual-status-chips").count(),
};
await shot(page, "polish_23_publication_not_ready_vl", "VL not falsely publication-ready");

const no404 = evidence.console_errors.filter((e) => /404|Failed to load/i.test(e));
evidence.notes.push(`console_errors=${evidence.console_errors.length}; likely404=${no404.length}`);
evidence.notes.push("VL publication must remain BLOCKED — aluminiu inactive");

fs.writeFileSync(
  path.join(__dirname, "final_polish_ui_capture_evidence.json"),
  JSON.stringify(evidence, null, 2),
);

await browser.close();
console.log("FINAL_POLISH_UI_CAPTURE_DONE", evidence.shots.length);
