/**
 * MOBILE-INT-01 Employee Mobile contract gate screenshots.
 * Requires mobile_int_01_runtime_gate_proof.py --setup first (employee link + assignments).
 */
const { chromium } = require("playwright");
const path = require("node:path");
const { execSync } = require("node:child_process");
const fs = require("node:fs");

const outDir = path.resolve(
  __dirname,
  "../../docs/qa/product-system-active-path-isolation-v1/mobile_int_01_screenshots",
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
  await page.waitForTimeout(800);
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

  const shots = [
    { file: "01_mobile_home_nav.png", url: `${BASE}/employee-app-v2`, note: "landing/navigation" },
    { file: "02_assigned_task_list.png", url: `${BASE}/employee-app-v2/tasks`, note: "assigned tasks" },
    { file: "03_task_detail.png", url: null, note: "task detail", dynamic: true },
    { file: "04_pipeline.png", url: `${BASE}/employee-app-v2/pipeline`, note: "pipeline context" },
    { file: "05_blockers.png", url: `${BASE}/employee-app-v2/blockers`, note: "blockers surface" },
    { file: "06_upcoming.png", url: `${BASE}/employee-app-v2/upcoming`, note: "upcoming/waiting" },
    { file: "07_personal.png", url: `${BASE}/employee-app-v2/personal`, note: "personal hub" },
    { file: "08_empty_or_error.png", url: `${BASE}/employee-app-v2/documents`, note: "documents/empty" },
  ];

  for (const shot of shots) {
    if (shot.dynamic) {
      await page.goto(`${BASE}/employee-app-v2/tasks`, { waitUntil: "networkidle" });
      await waitForMobileReady(page);
      const taskLink = page.locator('[data-testid^="employee-mobile-v2-task-row-"]').first();
      if (await taskLink.count()) {
        await taskLink.click();
        await page.waitForTimeout(1200);
        await page.screenshot({ path: path.join(outDir, shot.file), fullPage: true });
        const startBtn = page.getByTestId("employee-mobile-v2-work-room-start");
        if (await startBtn.count()) {
          await page.screenshot({
            path: path.join(outDir, "09_start_action_visible.png"),
            fullPage: true,
          });
        }
        const completeBtn = page.getByTestId("employee-mobile-v2-work-room-complete");
        if (await completeBtn.count()) {
          await page.screenshot({
            path: path.join(outDir, "10_complete_action_visible.png"),
            fullPage: true,
          });
        }
      } else {
        await page.screenshot({ path: path.join(outDir, shot.file), fullPage: true });
      }
      console.log(shot.file);
      continue;
    }
    await page.goto(shot.url, { waitUntil: "networkidle" });
    await waitForMobileReady(page);
    await page.screenshot({ path: path.join(outDir, shot.file), fullPage: true });
    console.log(shot.file);
  }

  // Structured error: attempt start on production-blocked order via UI if card exists
  await page.goto(`${BASE}/employee-app-v2/tasks`, { waitUntil: "networkidle" });
  await waitForMobileReady(page);
  await page.screenshot({ path: path.join(outDir, "11_tasks_refresh_state.png"), fullPage: true });

  await browser.close();
  console.log(`screenshots=${outDir}`);
})();
