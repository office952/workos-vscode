/**
 * P1 visual evidence — Playwright capture against live FE:3000 / BE:8000.
 * Run from frontend/: node ../docs/qa/.../capture_p1_screenshots.mjs
 */
import path from "node:path";
import { fileURLToPath } from "node:url";
import fs from "node:fs";
import { createRequire } from "node:module";

const require = createRequire(path.join(process.cwd(), "package.json"));
const { chromium } = require("playwright");

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const outDir = path.join(__dirname, "after");
fs.mkdirSync(outDir, { recursive: true });

const BASE = process.env.PW_BASE_URL || "http://127.0.0.1:3000";
const VL = "TPL-VOLUMETRIC-LETTERS_v2";
const detailUrl = `${BASE}/product-system/products/${encodeURIComponent(VL)}`;

async function settle(page, ms = 1800) {
  await page.waitForTimeout(ms);
}

async function openVlDetail(page) {
  await page.goto(detailUrl, { waitUntil: "domcontentloaded", timeout: 60000 });
  await settle(page, 2500);
  await page.waitForSelector('[data-testid="product-system-template-detail-panel"]', {
    timeout: 20000,
  });
}

async function clickTab(page, testId) {
  const tab = page.locator(`[data-testid="${testId}"]`);
  await tab.click({ timeout: 15000 });
  await settle(page, 2000);
}

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
await context.addInitScript(() => {
  try {
    sessionStorage.setItem("WORKOS_DEV_GUARD_BYPASS", "1");
  } catch {
    /* noop */
  }
});
const page = await context.newPage();

await page.goto(`${BASE}/product-system/products`, {
  waitUntil: "domcontentloaded",
  timeout: 60000,
});
await settle(page, 2500);
await page.screenshot({
  path: path.join(outDir, "01_ps_landing_products.png"),
  fullPage: false,
});
console.log("wrote 01");

await openVlDetail(page);
await page.screenshot({
  path: path.join(outDir, "02_ps_vl_detail_overview.png"),
  fullPage: false,
});
console.log("wrote 02");

await clickTab(page, "product-system-template-detail-tab-composition");
await page.waitForSelector('[data-testid="template-composition-authoring-panel"]', {
  timeout: 15000,
}).catch(() => null);
await page.screenshot({
  path: path.join(outDir, "03_ps_vl_composition.png"),
  fullPage: false,
});
console.log("wrote 03");

await clickTab(page, "product-system-template-detail-tab-readiness");
await page.waitForSelector('[data-testid="product-e2e-readiness-panel"]', {
  timeout: 15000,
}).catch(() => null);
await page.screenshot({
  path: path.join(outDir, "04_ps_vl_readiness.png"),
  fullPage: false,
});
console.log("wrote 04");

await clickTab(page, "product-system-template-detail-tab-publication");
await page.waitForSelector('[data-testid="product-template-publication-panel"]', {
  timeout: 15000,
}).catch(() => null);
await settle(page, 2500);
await page.screenshot({
  path: path.join(outDir, "05_ps_vl_publication_fail_closed.png"),
  fullPage: false,
});
console.log("wrote 05");

await clickTab(page, "product-system-template-detail-tab-runtime-preview");
await page.waitForSelector('[data-testid="template-runtime-preview-panel"]', {
  timeout: 15000,
}).catch(() => null);
await page.screenshot({
  path: path.join(outDir, "06_ps_vl_runtime_preview.png"),
  fullPage: false,
});
console.log("wrote 06");

for (const [name, url] of [
  ["07_workos_ref_settings_form.png", `${BASE}/settings`],
  ["08_workos_ref_quotes_list.png", `${BASE}/quotes`],
  ["09_workos_ref_intake_v6_operator.png", `${BASE}/intake-v6/operator`],
]) {
  await page.goto(url, { waitUntil: "domcontentloaded", timeout: 60000 });
  await settle(page, 2500);
  await page.screenshot({ path: path.join(outDir, name), fullPage: false });
  console.log("wrote", name);
}

await browser.close();
console.log("done", outDir);
