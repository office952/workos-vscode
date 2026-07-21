/**
 * Axis B face-treatment commercial path screenshots.
 * FE :3000 + BE :8000 required.
 */
import { createRequire } from "node:module";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(path.join(__dirname, "../../../../../frontend/package.json"));
const { chromium } = require("playwright");

const OUT = __dirname;
const FE = process.env.PW_BASE_URL ?? "http://127.0.0.1:3000";
const ACM = "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1";
const VIEWPORT = { width: 1440, height: 900 };

async function main() {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: VIEWPORT });
  const page = await context.newPage();
  const log = [];

  const shots = [
    { name: "01_acm_product_detail.png", url: `${FE}/product-system/products/${ACM}` },
    { name: "02_composition_tab_xor_preserved.png", url: `${FE}/product-system/products/${ACM}`, tab: "composition" },
  ];

  for (const shot of shots) {
    try {
      const resp = await page.goto(shot.url, { waitUntil: "networkidle", timeout: 25000 });
      await page.waitForTimeout(1000);
      if (shot.tab) {
        const tab = page.getByRole("button", { name: /compozi|composition/i }).first();
        if (await tab.count()) {
          await tab.click().catch(() => {});
          await page.waitForTimeout(600);
        }
        // Prefer data-testid if present
        const comp = page.locator('[data-testid="product-system-template-detail-composition"]');
        if (await comp.count()) {
          await comp.scrollIntoViewIfNeeded().catch(() => {});
        }
        const face = page.locator('[data-testid="acm-boxed-face-treatment-panel"]');
        if (await face.count()) {
          await face.scrollIntoViewIfNeeded().catch(() => {});
          await page.waitForTimeout(300);
        }
      }
      await page.screenshot({ path: path.join(OUT, shot.name), fullPage: true });
      const hasFace = (await page.locator('[data-testid="acm-boxed-face-treatment-panel"]').count()) > 0;
      const hasXor = (await page.locator('[data-testid="acm-boxed-applied-content-panel"]').count()) > 0;
      log.push({
        name: shot.name,
        url: shot.url,
        status: resp?.status() ?? null,
        ok: true,
        face_treatment_panel: hasFace,
        applied_content_panel: hasXor,
      });
    } catch (e) {
      log.push({ name: shot.name, url: shot.url, ok: false, error: String(e) });
    }
  }

  // Interactive both-enabled state if panel visible
  try {
    await page.goto(`${FE}/product-system/products/${ACM}`, { waitUntil: "networkidle", timeout: 25000 });
    await page.waitForTimeout(800);
    const face = page.locator('[data-testid="acm-boxed-face-treatment-panel"]');
    if (await face.count()) {
      await face.scrollIntoViewIfNeeded();
      await page.locator('[data-testid="acm-face-treatment-routed-checkbox"]').check({ force: true }).catch(() => {});
      await page.locator('[data-testid="acm-face-treatment-insert-checkbox"]').check({ force: true }).catch(() => {});
      await page.waitForTimeout(300);
      await page.screenshot({ path: path.join(OUT, "03_face_treatments_both_enabled.png"), fullPage: true });
      log.push({ name: "03_face_treatments_both_enabled.png", ok: true, coexistence: "both" });
    } else {
      log.push({ name: "03_face_treatments_both_enabled.png", ok: false, error: "panel_not_in_dom" });
    }
  } catch (e) {
    log.push({ name: "03_face_treatments_both_enabled.png", ok: false, error: String(e) });
  }

  fs.writeFileSync(path.join(OUT, "capture_log.json"), JSON.stringify(log, null, 2));
  await browser.close();
  console.log(JSON.stringify(log, null, 2));
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
