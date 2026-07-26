import path from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

const require = createRequire(path.join(process.cwd(), "package.json"));
const { chromium } = require("playwright");

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const out = path.join(__dirname, "after");
const BASE = process.env.PW_BASE_URL || "http://127.0.0.1:3000";
const VL = encodeURIComponent("TPL-VOLUMETRIC-LETTERS_v2");

const panels = [
  ["product-system-template-detail-tab-composition", "template-composition-authoring-panel", "03_ps_vl_composition.png"],
  ["product-system-template-detail-tab-readiness", "product-e2e-readiness-panel", "04_ps_vl_readiness.png"],
  ["product-system-template-detail-tab-publication", "product-template-publication-panel", "05_ps_vl_publication_fail_closed.png"],
  ["product-system-template-detail-tab-runtime-preview", "template-runtime-preview-panel", "06_ps_vl_runtime_preview.png"],
];

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1440, height: 1100 } });
await context.addInitScript(() => {
  sessionStorage.setItem("WORKOS_DEV_GUARD_BYPASS", "1");
});
const page = await context.newPage();
await page.goto(`${BASE}/product-system/products/${VL}`, {
  waitUntil: "domcontentloaded",
  timeout: 60000,
});
await page.waitForTimeout(2500);

for (const [tab, panel, file] of panels) {
  await page.locator(`[data-testid="${tab}"]`).click();
  await page.waitForTimeout(2000);
  const el = page.locator(`[data-testid="${panel}"]`);
  const count = await el.count();
  if (count > 0) {
    await el.first().scrollIntoViewIfNeeded();
    await page.waitForTimeout(400);
    await el.first().screenshot({ path: path.join(out, file) });
  } else {
    await page.screenshot({ path: path.join(out, file), fullPage: true });
  }
  console.log("wrote", file, "found", count);
}

await browser.close();
