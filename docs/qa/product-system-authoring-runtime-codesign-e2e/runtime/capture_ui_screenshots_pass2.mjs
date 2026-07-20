import { createRequire } from "node:module";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(path.join("C:", "w", "psiso", "frontend", "package.json"));
const { chromium } = require("playwright");
const OUT = path.resolve(__dirname, "../screenshots");

async function shot(page, name, note) {
  const dest = path.join(OUT, `${name}.png`);
  await page.screenshot({ path: dest, fullPage: true });
  console.log(`OK ${name}.png (${fs.statSync(dest).size}) ${note}`);
}

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

// Editor path for publication panels
await page.goto("http://127.0.0.1:3000/product-system/products/TPL-VOLUMETRIC-LETTERS_v2", {
  waitUntil: "domcontentloaded",
  timeout: 45000,
});
await page.waitForTimeout(4000);
const editor = page.getByTestId("product-system-template-detail-open-editor");
console.log("editor count", await editor.count());
if (await editor.count()) {
  await editor.first().click();
  await page.waitForTimeout(3500);
  await shot(page, "ui_13_template_editor_shell", "editor after open");
  const info = page.getByRole("button", { name: /Informații generale/i });
  if (await info.count()) {
    await info.first().click();
    await page.waitForTimeout(1500);
  }
  await shot(page, "ui_14_editor_informatii_generale", "Informații generale tab");
  const pub = page.getByTestId("product-template-publication-panel");
  const ready = page.getByTestId("product-e2e-readiness-panel");
  console.log("pub", await pub.count(), "ready", await ready.count());
  if (await pub.count()) {
    await pub.first().scrollIntoViewIfNeeded();
    await page.waitForTimeout(500);
    await shot(page, "ui_15_publication_panel", "publication panel");
  }
  if (await ready.count()) {
    await ready.first().scrollIntoViewIfNeeded();
    const btn = page.getByTestId("product-e2e-readiness-static-btn");
    if (await btn.count()) {
      await btn.first().click();
      await page.waitForTimeout(2500);
    }
    await shot(page, "ui_16_readiness_panel_blocked", "readiness after static");
  }
}

// Dossier — scroll for publication panels in rail
await page.goto("http://127.0.0.1:3000/product-system/blueprint-dossier", {
  waitUntil: "domcontentloaded",
  timeout: 45000,
});
await page.waitForTimeout(4000);
const pubD = page.getByTestId("product-template-publication-panel");
const readyD = page.getByTestId("product-e2e-readiness-panel");
console.log("dossier pub", await pubD.count(), "ready", await readyD.count());
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

// Intake — advance to Confirmare
await page.goto(
  "http://127.0.0.1:3000/intake-v6/a7b0162b-dc91-467f-aa24-c1279fb3a073/operator",
  { waitUntil: "domcontentloaded", timeout: 45000 }
);
await page.waitForTimeout(4000);
await shot(page, "ui_20_intake_configurare_fixture", "fixture IV6-DB2F86B7 configurare");
const continueBtn = page.getByRole("button", { name: /Continuă la Confirmare|Confirmare/i });
console.log("continue buttons", await continueBtn.count());
if (await continueBtn.count()) {
  await continueBtn.first().click();
  await page.waitForTimeout(3000);
  await shot(page, "ui_21_intake_confirmare_step", "after continue to confirm");
}
// direct hash/step attempts
for (const url of [
  "http://127.0.0.1:3000/intake-v6/a7b0162b-dc91-467f-aa24-c1279fb3a073/operator?step=3",
  "http://127.0.0.1:3000/intake-v6/a7b0162b-dc91-467f-aa24-c1279fb3a073/operator#confirm",
]) {
  await page.goto(url, { waitUntil: "domcontentloaded", timeout: 45000 });
  await page.waitForTimeout(2500);
  const t = await page.locator("body").innerText();
  if (/Confirmare finală|Confirmare draft|step=confirm|3 Confirmare/i.test(t)) {
    await shot(page, "ui_22_intake_confirmare_final", `matched confirm at ${url}`);
    break;
  }
}

await browser.close();
console.log("PASS2_DONE");
