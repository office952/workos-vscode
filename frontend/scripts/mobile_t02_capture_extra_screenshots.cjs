const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require("playwright");

const outDir = path.resolve(
  __dirname,
  "../../docs/qa/product-system-active-path-isolation-v1/mobile_t02_screenshots",
);
const BASE = "http://127.0.0.1:3000";

(async () => {
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 390, height: 844 },
    isMobile: true,
    hasTouch: true,
  });
  await context.addInitScript(() => sessionStorage.setItem("WORKOS_DEV_GUARD_BYPASS", "1"));
  const page = await context.newPage();

  await page.goto(`${BASE}/employee-app-v2/tasks`, { waitUntil: "networkidle" });
  await page.waitForSelector('[data-testid="employee-mobile-v2-tasks"]');
  await page.screenshot({ path: path.join(outDir, "10_assigned_in_progress.png"), fullPage: true });

  const detail = page.locator('[data-testid^="employee-mobile-v2-in-progress-row-"]').first();
  if (await detail.count()) {
    await detail.click();
    await page.waitForSelector('[data-testid="employee-mobile-v2-detail-production"]');
    await page.screenshot({ path: path.join(outDir, "11_production_block_detail.png"), fullPage: true });
  }

  await page.goto(`${BASE}/employee-app-v2/documents`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1200);
  await page.screenshot({ path: path.join(outDir, "09_valid_empty_documents.png"), fullPage: true });

  await page.goto(`${BASE}/employee-app-v2/tasks`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1200);
  await page.screenshot({ path: path.join(outDir, "12_refresh_stability.png"), fullPage: true });

  await browser.close();
  console.log("files:", fs.readdirSync(outDir).length);
})();
