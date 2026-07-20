/**
 * After-P0 screenshots — FE must proxy to BE with publication + readiness (BACKEND_PORT=8000).
 */
import { createRequire } from "node:module";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(path.join("C:", "w", "psiso", "frontend", "package.json"));
const { chromium } = require("playwright");

const OUT = path.join(__dirname, "after");
const FE = process.env.FE_BASE || "http://127.0.0.1:3021";
const VL = `${FE}/product-system/products/TPL-VOLUMETRIC-LETTERS_v2`;

fs.mkdirSync(OUT, { recursive: true });
const evidence = { fe: FE, captured_at: new Date().toISOString(), shots: [], notes: [] };

async function shot(page, name, note) {
  const dest = path.join(OUT, `${name}.png`);
  await page.screenshot({ path: dest, fullPage: true });
  evidence.shots.push({ name, note, size: fs.statSync(dest).size });
  console.log(`OK ${name}`);
}

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

await page.goto(`${FE}/product-system/products`, { waitUntil: "domcontentloaded", timeout: 60000 });
await page.waitForTimeout(2500);
await shot(page, "01_shell_nav_in_dezvoltare", "Shell: Products primary + În dezvoltare cluster");

await page.goto(`${FE}/product-system/components`, { waitUntil: "domcontentloaded", timeout: 60000 });
await page.waitForTimeout(1200);
await shot(page, "02_section_in_dezvoltare", "Non-operational section badge renamed");

await page.goto(VL, { waitUntil: "domcontentloaded", timeout: 60000 });
await page.waitForTimeout(3500);
await shot(page, "03_vl_header_next_action", "VL header lifecycle/publication + next-action strip");

const pubTab = page.getByTestId("product-system-template-detail-tab-publication");
if (await pubTab.count()) {
  await pubTab.first().click();
  await page.waitForTimeout(2500);
  await shot(page, "04_vl_publication_fail_closed", "Publică disabled + primary blocker");
} else {
  evidence.notes.push("MISSING publication tab");
}

const readyTab = page.getByTestId("product-system-template-detail-tab-readiness");
if (await readyTab.count()) {
  await readyTab.first().click();
  await page.waitForTimeout(1500);
  const btn = page.getByTestId("product-e2e-readiness-static-btn");
  if (await btn.count()) {
    await btn.first().click();
    await page.waitForTimeout(2500);
  }
  await shot(page, "05_vl_readiness_blocked", "Pregătire E2E BLOCKED");
}

fs.writeFileSync(path.join(OUT, "capture_evidence.json"), JSON.stringify(evidence, null, 2));
await browser.close();
console.log("DONE", evidence.shots.length, "shots");
