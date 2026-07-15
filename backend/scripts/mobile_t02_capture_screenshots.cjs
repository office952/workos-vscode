/**
 * MOBILE-T02 assigned/available task list + detail screenshots.
 * Requires backend :8001, frontend :3000, Sandu employee link (INT-01 setup).
 */
const { chromium } = require("playwright");
const path = require("node:path");
const { execSync } = require("node:child_process");
const fs = require("node:fs");

const outDir = path.resolve(
  __dirname,
  "../../docs/qa/product-system-active-path-isolation-v1/mobile_t02_screenshots",
);
const BASE = "http://127.0.0.1:3000";
const PYTHON = path.resolve(__dirname, "../.venv/Scripts/python.exe");
const MOBILE_VIEWPORT = { width: 390, height: 844 };

function runGateSetup() {
  execSync(`"${PYTHON}" scripts/mobile_int_01_runtime_gate_proof.py --setup`, {
    cwd: path.resolve(__dirname, ".."),
    stdio: "inherit",
    env: {
      ...process.env,
      APP_ENV: "development",
      ENVIRONMENT: "development",
      DATABASE_URL: "sqlite+aiosqlite:///./dev.db",
      JWT_SECRET_KEY: "local-dev-secret-not-for-production",
    },
  });
}

async function waitForMobileReady(page) {
  await page.waitForSelector('[data-testid="employee-mobile-v2-standalone-root"]', {
    timeout: 60000,
  });
  await page.waitForTimeout(1000);
}

(async () => {
  fs.mkdirSync(outDir, { recursive: true });
  runGateSetup();

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: MOBILE_VIEWPORT,
    isMobile: true,
    hasTouch: true,
  });
  await context.addInitScript(() => sessionStorage.setItem("WORKOS_DEV_GUARD_BYPASS", "1"));
  const page = await context.newPage();

  await page.goto(`${BASE}/employee-app-v2/tasks`, { waitUntil: "networkidle" });
  await waitForMobileReady(page);
  await page.screenshot({ path: path.join(outDir, "01_tasks_assigned_sections.png"), fullPage: true });

  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await page.waitForTimeout(500);
  await page.screenshot({ path: path.join(outDir, "02_tasks_available_section.png"), fullPage: true });

  const rootRow = page.locator('[data-testid*="vector_prep"]').first();
  if (await rootRow.count()) {
    await rootRow.scrollIntoViewIfNeeded();
    await page.screenshot({ path: path.join(outDir, "03_root_task_card.png"), fullPage: false });
  }

  const mountingRow = page.locator('[data-testid*="mounting"]').first();
  if (await mountingRow.count()) {
    await mountingRow.scrollIntoViewIfNeeded();
    await page.screenshot({ path: path.join(outDir, "04_mounting_task_card.png"), fullPage: false });
  }

  const logoRow = page.locator('[data-testid*="logo"]').first();
  if (await logoRow.count()) {
    await logoRow.scrollIntoViewIfNeeded();
    await page.screenshot({ path: path.join(outDir, "05_logo_task_card.png"), fullPage: false });
  }

  const firstAssigned = page.locator('[data-testid^="employee-mobile-v2-task-row-"], [data-testid^="employee-mobile-v2-in-progress-row-"]').first();
  if (await firstAssigned.count()) {
    await firstAssigned.click();
    await page.waitForTimeout(1200);
    await page.screenshot({ path: path.join(outDir, "06_task_detail_identity.png"), fullPage: true });
    await page.screenshot({ path: path.join(outDir, "07_task_detail_readiness.png"), fullPage: true });
    await page.screenshot({ path: path.join(outDir, "08_task_detail_production_block.png"), fullPage: true });
  }

  await browser.close();
  console.log(`MOBILE-T02 screenshots saved to ${outDir}`);
})();
