/**
 * FINAL COMPLETION GATE — capture Publication/Readiness on real template Lifecycle tab.
 * Uses FE 3000; proxy target must be BACKEND_PORT (canonical 8001).
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
const VL = `${FE}/product-system/products/TPL-VOLUMETRIC-LETTERS_v2`;

async function shot(page, name, note) {
  const dest = path.join(OUT, `${name}.png`);
  await page.screenshot({ path: dest, fullPage: true });
  console.log(`OK ${name}.png (${fs.statSync(dest).size}) ${note}`);
}

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
const evidence = { fe: FE, route: VL, panels: {}, proxy_checks: [] };

// Proxy smoke via page request
await page.goto(VL, { waitUntil: "domcontentloaded", timeout: 60000 });
await page.waitForTimeout(3500);
await shot(page, "ui_01_product_system_catalog_or_detail", "VL deep link overview");

const lifecycleTab = page.getByTestId("product-system-template-detail-tab-lifecycle");
evidence.panels.lifecycle_tab = await lifecycleTab.count();
if (await lifecycleTab.count()) {
  await lifecycleTab.first().click();
  await page.waitForTimeout(2000);
  await shot(page, "ui_03_template_lifecycle_tab", "Lifecycle tab with mounted panels");

  const pub = page.getByTestId("product-template-publication-panel");
  const ready = page.getByTestId("product-e2e-readiness-panel");
  evidence.panels.publication = await pub.count();
  evidence.panels.readiness = await ready.count();
  console.log("lifecycle pub", evidence.panels.publication, "ready", evidence.panels.readiness);

  if (await pub.count()) {
    await pub.first().scrollIntoViewIfNeeded();
    await page.waitForTimeout(400);
    await shot(page, "ui_04_publication_panel_lifecycle", "Publication on template Lifecycle");
  }
  if (await ready.count()) {
    await ready.first().scrollIntoViewIfNeeded();
    const btn = page.getByTestId("product-e2e-readiness-static-btn");
    if (await btn.count()) {
      await btn.first().click();
      await page.waitForTimeout(3000);
    }
    await shot(page, "ui_05_readiness_panel_lifecycle", "Readiness on template Lifecycle");
    const dual = page.getByTestId("product-e2e-readiness-dual-axes");
    evidence.panels.dual_axes = await dual.count();
  }
}

await page.goto(`${FE}/product-system/products`, {
  waitUntil: "domcontentloaded",
  timeout: 45000,
});
await page.waitForTimeout(2500);
await shot(page, "ui_01_product_system_catalog", "catalog landing");

await page.goto(`${FE}/product-system/blueprint-dossier`, {
  waitUntil: "domcontentloaded",
  timeout: 45000,
});
await page.waitForTimeout(3500);
const pubD = page.getByTestId("product-template-publication-panel");
const readyD = page.getByTestId("product-e2e-readiness-panel");
evidence.panels.dossier_publication = await pubD.count();
evidence.panels.dossier_readiness = await readyD.count();
if (await pubD.count()) {
  await pubD.first().scrollIntoViewIfNeeded();
  await shot(page, "ui_17_dossier_publication_panel", "dossier publication");
}
if (await readyD.count()) {
  await readyD.first().scrollIntoViewIfNeeded();
  const btn = page.getByTestId("product-e2e-readiness-static-btn");
  if (await btn.count()) {
    await btn.first().click();
    await page.waitForTimeout(2500);
  }
  await shot(page, "ui_18_dossier_readiness_panel", "dossier readiness");
}
await shot(page, "ui_19_dossier_fullpage", "dossier full");

// Proxy status from browser
const proxyStatus = await page.evaluate(async () => {
  try {
    const r = await fetch("/api/v1/product-system/template-availability");
    return { ok: r.ok, status: r.status, url: r.url };
  } catch (e) {
    return { ok: false, error: String(e) };
  }
});
evidence.proxy_checks.push(proxyStatus);
console.log("proxy", JSON.stringify(proxyStatus));

fs.writeFileSync(
  path.join(__dirname, "completion_gate_ui_capture_evidence.json"),
  JSON.stringify(evidence, null, 2),
);

await browser.close();
console.log("COMPLETION_GATE_UI_CAPTURE_DONE");
