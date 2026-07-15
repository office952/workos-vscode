/**
 * W7-INT-01 frozen-spine integration gate screenshots.
 * Execution chain on order 23099; QSN2/quote 1 read-only reference.
 */
const { chromium } = require("playwright");
const path = require("node:path");
const { execSync } = require("node:child_process");
const fs = require("node:fs");

const outDir = path.resolve(
  __dirname,
  "../../docs/qa/product-system-active-path-isolation-v1/w7_int_01_screenshots",
);
const BASE = "http://127.0.0.1:3000";
const API = "http://127.0.0.1:8001";
const ORDER = 23099;
const BLOCKER = "INTERNAL_SABLON_FOREX_COST";
const PYTHON = path.resolve(__dirname, "../.venv/Scripts/python.exe");
const DEV_HEADERS = {
  Authorization: "Bearer __DEV_BYPASS_TOKEN__",
  Origin: "http://127.0.0.1:3000",
  "Content-Type": "application/json",
};

function resetExecutionFixture() {
  execSync(
    `"${PYTHON}" -c "import asyncio; from scripts.w5_int_02_runtime_e2e_gate_proof import _reset_gate_fixture; print(asyncio.run(_reset_gate_fixture()))"`,
    {
      cwd: path.resolve(__dirname, ".."),
      stdio: "inherit",
      env: {
        ...process.env,
        APP_ENV: "development",
        ENVIRONMENT: "development",
        DATABASE_URL: "sqlite+aiosqlite:///./dev.db",
        JWT_SECRET_KEY: "local-dev-secret-not-for-production",
      },
    },
  );
}

async function resolveApi(code, note) {
  await fetch(`${API}/api/v1/execution/orders/${ORDER}/owner-decisions/${code}/resolve`, {
    method: "POST",
    headers: DEV_HEADERS,
    body: JSON.stringify({ status: "resolved", note }),
  });
}

async function ensureExecutionPlan() {
  await fetch(`${API}/api/v1/execution/plan-v2/from-order/${ORDER}`, {
    method: "POST",
    headers: DEV_HEADERS,
  });
  await fetch(`${API}/api/v1/execution/plan-v2/materialize-tasks/${ORDER}`, {
    method: "POST",
    headers: DEV_HEADERS,
  });
}

async function openExecution(page) {
  await ensureExecutionPlan();
  await page.goto(`${BASE}/execution/${ORDER}`, { waitUntil: "networkidle" });
  await page.waitForSelector('[data-testid="operator-production-release-summary"]', { timeout: 60000 });
  await page.getByTestId("operator-production-release-details-toggle").click().catch(() => {});
}

(async () => {
  fs.mkdirSync(outDir, { recursive: true });
  resetExecutionFixture();

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  await context.addInitScript(() => sessionStorage.setItem("WORKOS_DEV_GUARD_BYPASS", "1"));
  const page = await context.newPage();

  await page.goto(`${BASE}/intake-v2`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1200);
  await page.screenshot({ path: path.join(outDir, "01_intake_request_surface.png"), fullPage: true });
  console.log("01");

  await page.goto(`${BASE}/product-system`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1200);
  await page.screenshot({ path: path.join(outDir, "02_product_definition_surface.png"), fullPage: true });
  console.log("02");

  await openExecution(page);
  await page.getByText("Vector Prep").first().scrollIntoViewIfNeeded().catch(() => {});
  await page.screenshot({ path: path.join(outDir, "03_execution_plan_task_identity.png"), fullPage: true });
  console.log("03");

  await page.getByTestId("operator-production-release-status").scrollIntoViewIfNeeded();
  await page.screenshot({ path: path.join(outDir, "04_blocked_production_strip.png"), fullPage: true });
  console.log("04");

  const note = page.locator(`[data-testid="owner-decision-resolve-note-${BLOCKER}"]`);
  if (await note.count()) {
    await note.fill("W7-INT-01 partial resolve gate.");
    await page.locator(`[data-testid="owner-decision-resolve-submit-${BLOCKER}"]`).click();
    await page.waitForTimeout(2000);
  }
  await page.screenshot({ path: path.join(outDir, "05_partial_resolution_still_blocked.png"), fullPage: true });
  console.log("05");

  await resolveApi("INTERNAL_MONTAJ_RULE", "W7-INT-01 montaj.");
  await resolveApi("INTERNAL_CONSUMABLES_RULE", "W7-INT-01 consumabile.");
  await page.reload({ waitUntil: "networkidle" });
  await page.getByTestId("operator-production-release-details-toggle").click().catch(() => {});
  await page.waitForTimeout(800);
  await page.screenshot({ path: path.join(outDir, "06_full_resolution_allowed.png"), fullPage: true });
  console.log("06");

  await page.getByText("Rezolvat de:").first().scrollIntoViewIfNeeded().catch(() => {});
  await page.screenshot({ path: path.join(outDir, "07_manager_resolution_metadata.png"), fullPage: true });
  console.log("07");

  await page.goto(`${BASE}/operator?orderId=${ORDER}`, { waitUntil: "networkidle" });
  await page.waitForSelector('[data-testid="operator-production-release-status"]', { timeout: 60000 });
  await page.screenshot({ path: path.join(outDir, "08_operator_readonly_state.png"), fullPage: true });
  console.log("08");

  await openExecution(page);
  await page.screenshot({ path: path.join(outDir, "09_startable_task_after_resolution.png"), fullPage: true });
  console.log("09");

  const startRes = await fetch(`${API}/api/v1/execution/reality/start-task`, {
    method: "POST",
    headers: DEV_HEADERS,
    body: JSON.stringify({
      order_id: ORDER,
      task_id: "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:vector_prep",
      timestamp: new Date().toISOString(),
    }),
  });
  console.log("start", startRes.status);
  await page.reload({ waitUntil: "networkidle" });
  await page.screenshot({ path: path.join(outDir, "10_execution_reality_state.png"), fullPage: true });
  console.log("10");

  await page.goto(`${BASE}/quotes/1`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1500);
  await page.screenshot({ path: path.join(outDir, "11_frozen_offer_quote_identity.png"), fullPage: true });
  console.log("11");

  await openExecution(page);
  await page.getByTestId(`owner-decision-code-${BLOCKER}`).scrollIntoViewIfNeeded().catch(() => {});
  await page.screenshot({ path: path.join(outDir, "12_snapshot_identity_stable.png"), fullPage: true });
  console.log("12");

  await page.goto(`${BASE}/execution/${ORDER}`, { waitUntil: "networkidle" });
  await page.getByRole("button", { name: "Refresh" }).click().catch(() => {});
  await page.waitForTimeout(800);
  await page.screenshot({ path: path.join(outDir, "13_refresh_stability.png"), fullPage: true });
  console.log("13");

  await browser.close();
})();
