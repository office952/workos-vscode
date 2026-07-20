/**
 * READ-ONLY UI truth audit screenshots — no product data writes.
 * Captures Product System + WorkOS reference pages.
 */
import { createRequire } from "node:module";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(path.join("C:", "w", "psiso", "frontend", "package.json"));
const { chromium } = require("playwright");

const OUT = __dirname;
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

async function shot(page, name, note, opts = {}) {
  const dest = path.join(OUT, `${name}.png`);
  await page.screenshot({ path: dest, fullPage: Boolean(opts.fullPage), ...opts });
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

// 01 Landing products
await page.goto(`${FE}/product-system/products`, { waitUntil: "domcontentloaded", timeout: 60000 });
await page.waitForTimeout(2500);
await shot(page, "01_ps_landing_products", "Landing /product-system/products", { fullPage: true });

// 02 Planned section (Planificat)
await page.goto(`${FE}/product-system/components`, { waitUntil: "domcontentloaded", timeout: 60000 });
await page.waitForTimeout(1500);
await shot(page, "02_ps_planificat_components", "Planificat section Components", { fullPage: true });

// 03 Nav strip with Planificat badges
await page.goto(`${FE}/product-system/products`, { waitUntil: "domcontentloaded", timeout: 60000 });
await page.waitForTimeout(1500);
const nav = page.getByTestId("product-system-shell-nav");
if (await nav.count()) {
  await nav.first().scrollIntoViewIfNeeded();
  await shot(page, "03_ps_shell_nav_planificat_badges", "Shell nav Planificat badges");
} else {
  evidence.notes.push("MISSING shell nav");
}

// 04 VL template overview
await page.goto(VL, { waitUntil: "domcontentloaded", timeout: 60000 });
await page.waitForTimeout(3000);
await shot(page, "04_vl_template_overview_dual_chips", "VL overview + dual status chips", {
  fullPage: true,
});

// 05 Composition
await clickTab(page, "product-system-template-detail-tab-composition");
await shot(page, "05_vl_composition", "Composition tab", { fullPage: true });

// 06 Contracts
await clickTab(page, "product-system-template-detail-tab-contracts");
await shot(page, "06_vl_contracts", "Contracts tab", { fullPage: true });

// 07 Dossier tab
await clickTab(page, "product-system-template-detail-tab-dossier");
await shot(page, "07_vl_dossier_tab", "Dossier tab + Studio CTA", { fullPage: true });

// 08 Blueprint dossier
await page.goto(`${FE}/product-system/blueprint-dossier?template=${encodeURIComponent(VL_CODE)}`, {
  waitUntil: "domcontentloaded",
  timeout: 60000,
});
await page.waitForTimeout(3500);
await shot(page, "08_blueprint_dossier_studio", "Blueprint Dossier Studio deep-link", {
  fullPage: true,
});

// 09 Sticky footer
const footer = page.getByTestId("blueprint-dossier-sticky-publish-footer");
if (await footer.count()) {
  await footer.first().scrollIntoViewIfNeeded();
  await page.waitForTimeout(300);
  await shot(page, "09_sticky_save_validate_check_publish", "Sticky Salvează→Validează→Verifică→Publică");
} else {
  evidence.notes.push("MISSING sticky footer");
}

// 10 Runtime preview
await page.goto(VL, { waitUntil: "domcontentloaded", timeout: 60000 });
await page.waitForTimeout(2500);
await clickTab(page, "product-system-template-detail-tab-runtime-preview");
await shot(page, "10_vl_runtime_preview", "Runtime Preview", { fullPage: true });

// 11 Readiness
await clickTab(page, "product-system-template-detail-tab-readiness");
const readyBtn = page.getByTestId("product-e2e-readiness-static-btn");
if (await readyBtn.count()) {
  await readyBtn.first().click();
  await page.waitForTimeout(3500);
}
await shot(page, "11_vl_readiness_system_link", "Readiness + System Link Check", { fullPage: true });

// 12 Publication
await clickTab(page, "product-system-template-detail-tab-publication");
await page.waitForTimeout(1500);
await shot(page, "12_vl_publication", "Publication panel", { fullPage: true });

// 13 WorkOS ref — Inventory
await page.goto(`${FE}/inventory`, { waitUntil: "domcontentloaded", timeout: 60000 });
await page.waitForTimeout(2500);
await shot(page, "13_workos_ref_inventory", "WorkOS reference: Inventory", { fullPage: true });

// 14 WorkOS ref — Governance or Settings (admin-ish)
await page.goto(`${FE}/governance`, { waitUntil: "domcontentloaded", timeout: 60000 });
await page.waitForTimeout(2000);
await shot(page, "14_workos_ref_governance", "WorkOS reference: Governance", { fullPage: true });

// 15 WorkOS ref — Work Intake list if exists
for (const route of ["/work-intake", "/intake-v2", "/intake"]) {
  const res = await page.goto(`${FE}${route}`, { waitUntil: "domcontentloaded", timeout: 30000 }).catch(() => null);
  if (res && res.status() < 400) {
    await page.waitForTimeout(2000);
    const url = page.url();
    if (!url.includes("login") && !url.endsWith("/dashboard")) {
      await shot(page, "15_workos_ref_intake", `WorkOS reference intake route ${route}`, {
        fullPage: true,
      });
      break;
    }
  }
}

fs.writeFileSync(path.join(OUT, "capture_evidence.json"), JSON.stringify(evidence, null, 2));
console.log(JSON.stringify({ shots: evidence.shots.length, notes: evidence.notes, errors: evidence.console_errors.length }, null, 2));
await browser.close();
