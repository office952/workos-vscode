/**
 * Honest UI screenshot pack for Product System closure (Agent C).
 * Captures reachable surfaces; documents auth/environment failures without faking.
 */
import { createRequire } from "node:module";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(path.join("C:", "w", "psiso", "frontend", "package.json"));
const { chromium } = require("playwright");
const OUT = path.resolve(__dirname, "../screenshots");
const BASE = process.env.WORKOS_FE_BASE || "http://127.0.0.1:3000";
const TEMPLATE = process.env.WORKOS_PS_TEMPLATE || "TPL-VOLUMETRIC-LETTERS_v2";
const WORKSPACE =
  process.env.WORKOS_IV6_WORKSPACE || "a7b0162b-dc91-467f-aa24-c1279fb3a073";

fs.mkdirSync(OUT, { recursive: true });

const inventory = [];

async function shot(page, name, note) {
  const file = `${name}.png`;
  const dest = path.join(OUT, file);
  await page.screenshot({ path: dest, fullPage: true });
  const st = fs.statSync(dest);
  inventory.push({ file, bytes: st.size, url: page.url(), note: note || "" });
  console.log(`OK ${file} (${st.size}) ${note || ""}`);
}

async function safeGoto(page, url, waitMs = 4000) {
  const resp = await page.goto(url, { waitUntil: "domcontentloaded", timeout: 45000 });
  await page.waitForTimeout(waitMs);
  return resp;
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    locale: "ro-RO",
  });
  const page = await context.newPage();

  // 1 Catalog
  await safeGoto(page, `${BASE}/product-system/products`);
  await shot(page, "ui_01_product_system_catalog", "catalog list");

  // 2 Template detail
  await safeGoto(page, `${BASE}/product-system/products/${TEMPLATE}`, 5000);
  const bodyText = await page.locator("body").innerText().catch(() => "");
  if (/Se verifică sesiunea|Autentificare|Login|Unauthorized/i.test(bodyText) && bodyText.length < 400) {
    await shot(page, "ui_02_auth_blocked_template_detail", "ENVIRONMENT_FAILURE auth gate");
  } else {
    await shot(page, "ui_02_template_detail_volumetric", "template detail default tab");

    // Click Lifecycle / Informații if present
    const lifecycle = page.getByRole("tab", { name: /Lifecycle/i });
    if (await lifecycle.count()) {
      await lifecycle.first().click();
      await page.waitForTimeout(1500);
      await shot(page, "ui_03_template_lifecycle_tab", "Lifecycle tab");
    }

    const infoGen = page.getByRole("button", { name: /Informații generale/i });
    if (await infoGen.count()) {
      await infoGen.first().click();
      await page.waitForTimeout(1500);
      await shot(page, "ui_04_template_informatii_generale", "Informații generale (publication host)");
    }

    // Scroll to publication / readiness panels if present
    const pub = page.getByTestId("product-template-publication-panel");
    const ready = page.getByTestId("product-e2e-readiness-panel");
    if (await pub.count()) {
      await pub.first().scrollIntoViewIfNeeded();
      await page.waitForTimeout(800);
      await shot(page, "ui_05_publication_panel", "publication panel in view");
    } else {
      inventory.push({
        file: "ui_05_publication_panel.png",
        bytes: 0,
        url: page.url(),
        note: "MISSING — panel not in DOM on current surface",
      });
      console.log("MISSING ui_05_publication_panel");
    }

    if (await ready.count()) {
      await ready.first().scrollIntoViewIfNeeded();
      // Try static check
      const btn = page.getByTestId("product-e2e-readiness-static-btn");
      if (await btn.count()) {
        await btn.first().click();
        await page.waitForTimeout(2500);
      }
      await shot(page, "ui_06_readiness_panel", "readiness panel after static check attempt");
    } else {
      inventory.push({
        file: "ui_06_readiness_panel.png",
        bytes: 0,
        url: page.url(),
        note: "MISSING — panel not in DOM on current surface",
      });
      console.log("MISSING ui_06_readiness_panel");
    }

    const dossierTab = page.getByRole("tab", { name: /^Dossier$/i });
    if (await dossierTab.count()) {
      await dossierTab.first().click();
      await page.waitForTimeout(1500);
      await shot(page, "ui_07_template_dossier_tab", "template Dossier tab");
    }
  }

  // 3 Blueprint Dossier Studio
  await safeGoto(page, `${BASE}/product-system/blueprint-dossier`, 5000);
  await shot(page, "ui_08_blueprint_dossier_studio", "dossier studio shell");
  const sticky = page.getByTestId("blueprint-dossier-sticky-publish-footer");
  if (await sticky.count()) {
    await sticky.first().scrollIntoViewIfNeeded();
    await page.waitForTimeout(500);
    await shot(page, "ui_09_dossier_sticky_footer", "sticky publish footer");
  } else {
    inventory.push({
      file: "ui_09_dossier_sticky_footer.png",
      bytes: 0,
      url: page.url(),
      note: "MISSING — sticky footer not visible (empty state or auth)",
    });
    console.log("MISSING ui_09_dossier_sticky_footer");
  }

  // 4 Intake Confirmare
  await safeGoto(page, `${BASE}/intake-v6/${WORKSPACE}/operator?step=confirm`, 5000);
  const intakeText = await page.locator("body").innerText().catch(() => "");
  if (/chrome-error|Se verifică sesiunea|Autentificare|Login/i.test(intakeText) && intakeText.length < 500) {
    await shot(page, "ui_10_intake_confirm_auth_or_error", "ENVIRONMENT_FAILURE or auth on Confirmare");
  } else {
    await shot(page, "ui_10_intake_confirmare", "Intake Confirmare reachable");
  }

  // Also try without query
  await safeGoto(page, `${BASE}/intake-v6/operator`, 4000);
  await shot(page, "ui_11_intake_operator_shell", "Intake operator shell");

  await browser.close();

  const indexPath = path.join(OUT, "SCREENSHOT_INVENTORY.md");
  const lines = [
    "# Screenshot inventory — Agent C UI pack",
    "",
    `| Field | Value |`,
    `|---|---|`,
    `| Date | 2026-07-20 |`,
    `| FE base | ${BASE} |`,
    `| Template | ${TEMPLATE} |`,
    `| Workspace | ${WORKSPACE} |`,
    "",
    "| File | Bytes | URL | Note |",
    "|---|---:|---|---|",
    ...inventory.map(
      (r) => `| \`${r.file}\` | ${r.bytes} | ${r.url} | ${r.note.replace(/\|/g, "/")} |`
    ),
    "",
  ];
  fs.writeFileSync(indexPath, lines.join("\n"), "utf8");
  console.log(`Wrote ${indexPath}`);
  console.log(JSON.stringify({ count: inventory.length, inventory }, null, 2));
}

main().catch((err) => {
  console.error("CAPTURE_FAIL", err);
  process.exit(1);
});
