/**
 * W6-T04 manager resolution UI screenshots.
 * Prerequisite: stack on :3000 / :8001 with VITE_ENABLE_DEV_AUTH=true (start-dev.ps1).
 */
const { chromium } = require("playwright");
const path = require("node:path");
const { execSync } = require("node:child_process");
const fs = require("node:fs");

const outDir = path.resolve(
  __dirname,
  "../../docs/qa/product-system-active-path-isolation-v1/w6_t04_screenshots",
);

const BASE = "http://127.0.0.1:3000";
const API = "http://127.0.0.1:8001";
const ORDER = 23150;
const BLOCKER = "INTERNAL_SABLON_FOREX_COST";
const DEV_HEADERS = {
  Authorization: "Bearer __DEV_BYPASS_TOKEN__",
  Origin: "http://127.0.0.1:3000",
  "Content-Type": "application/json",
};
const PYTHON = path.resolve(__dirname, "../.venv/Scripts/python.exe");

async function resetFixture() {
  execSync(`"${PYTHON}" scripts/w6_t03_blocked_fixture_setup.py`, {
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

async function resolveViaApi(code, note) {
  const res = await fetch(
    `${API}/api/v1/execution/orders/${ORDER}/owner-decisions/${code}/resolve`,
    {
      method: "POST",
      headers: DEV_HEADERS,
      body: JSON.stringify({ status: "resolved", note }),
    },
  );
  return res.json();
}

async function openExecutionDetails(page) {
  await page.goto(`${BASE}/execution/${ORDER}`, { waitUntil: "networkidle" });
  await page.waitForSelector('[data-testid="operator-production-release-summary"]', {
    timeout: 60000,
  });
  await page.getByTestId("operator-production-release-details-toggle").click();
  await page.waitForSelector('[data-testid="operator-owner-decision-details"]', { timeout: 15000 });
  await page.waitForSelector(`[data-testid="owner-decision-row-${BLOCKER}"]`, { timeout: 15000 });
}

(async () => {
  fs.mkdirSync(outDir, { recursive: true });
  await resetFixture();

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  await context.addInitScript(() => {
    sessionStorage.setItem("WORKOS_DEV_GUARD_BYPASS", "1");
  });
  const page = await context.newPage();

  await openExecutionDetails(page);
  await page.screenshot({
    path: path.join(outDir, "01_manager_unresolved_resolve_action.png"),
    fullPage: true,
  });
  console.log("saved 01_manager_unresolved_resolve_action.png");

  await page.goto(`${BASE}/operator?orderId=${ORDER}`, { waitUntil: "networkidle" });
  await page.waitForSelector('[data-testid="operator-production-release-status"]', {
    timeout: 60000,
  });
  await page.getByTestId("operator-production-release-details-toggle").click();
  await page.waitForSelector('[data-testid="operator-owner-decision-details"]', { timeout: 15000 });
  await page.waitForTimeout(400);
  await page.screenshot({
    path: path.join(outDir, "02_operator_readonly_no_resolve.png"),
    fullPage: true,
  });
  console.log("saved 02_operator_readonly_no_resolve.png");

  await openExecutionDetails(page);
  const note = page.locator(`[data-testid="owner-decision-resolve-note-${BLOCKER}"]`);
  await note.waitFor({ timeout: 15000 });
  await note.fill("W6-T04 screenshot: rezolvare Forex operationala.");
  await page.screenshot({
    path: path.join(outDir, "03_resolution_form_with_note.png"),
    fullPage: true,
  });
  console.log("saved 03_resolution_form_with_note.png");

  await page.locator(`[data-testid="owner-decision-resolve-submit-${BLOCKER}"]`).click();
  await page.waitForTimeout(2000);
  await page.screenshot({
    path: path.join(outDir, "04_after_one_blocker_resolved.png"),
    fullPage: true,
  });
  console.log("saved 04_after_one_blocker_resolved.png");

  await page.getByTestId("operator-production-blocker-count").scrollIntoViewIfNeeded();
  await page.screenshot({
    path: path.join(outDir, "05_partial_blocked_remaining_count.png"),
    fullPage: true,
  });
  console.log("saved 05_partial_blocked_remaining_count.png");

  await resolveViaApi("INTERNAL_MONTAJ_RULE", "W6-T04 screenshot: Montaj rezolvat.");
  await resolveViaApi("INTERNAL_CONSUMABLES_RULE", "W6-T04 screenshot: Consumabile rezolvat.");

  await page.reload({ waitUntil: "networkidle" });
  await page.waitForSelector('[data-testid="operator-production-release-summary"]', { timeout: 60000 });
  await page.getByTestId("operator-production-release-details-toggle").click();
  await page.waitForTimeout(800);
  await page.screenshot({
    path: path.join(outDir, "06_all_production_blockers_resolved.png"),
    fullPage: true,
  });
  console.log("saved 06_all_production_blockers_resolved.png");

  await page.getByTestId("operator-production-release-status").scrollIntoViewIfNeeded();
  await page.screenshot({
    path: path.join(outDir, "07_production_allowed_strip.png"),
    fullPage: true,
  });
  console.log("saved 07_production_allowed_strip.png");

  await page.getByText("Rezolvat de:").first().scrollIntoViewIfNeeded();
  await page.screenshot({
    path: path.join(outDir, "08_resolver_timestamp_metadata.png"),
    fullPage: true,
  });
  console.log("saved 08_resolver_timestamp_metadata.png");

  await page.goto(`${BASE}/operator?orderId=${ORDER}`, { waitUntil: "networkidle" });
  await page.waitForSelector('[data-testid="operator-production-release-status"]', { timeout: 60000 });
  await page.screenshot({
    path: path.join(outDir, "09_operator_view_refreshed_allowed.png"),
    fullPage: true,
  });
  console.log("saved 09_operator_view_refreshed_allowed.png");

  await openExecutionDetails(page);
  await page.getByTestId(`owner-decision-code-${BLOCKER}`).scrollIntoViewIfNeeded();
  await page.screenshot({
    path: path.join(outDir, "10_frozen_snapshot_identity_unchanged.png"),
    fullPage: true,
  });
  console.log("saved 10_frozen_snapshot_identity_unchanged.png");

  await resetFixture();
  await resolveViaApi(BLOCKER, "W6-T04 idempotent probe note.");
  await openExecutionDetails(page);
  await page.waitForSelector(`[data-testid="owner-decision-resolved-state-${BLOCKER}"]`, {
    timeout: 15000,
  });
  await page.screenshot({
    path: path.join(outDir, "11_idempotent_resolved_state.png"),
    fullPage: true,
  });
  console.log("saved 11_idempotent_resolved_state.png");

  await resetFixture();
  await openExecutionDetails(page);
  await page.route(`**/owner-decisions/${BLOCKER}/resolve`, async (route) => {
    await route.fulfill({
      status: 403,
      contentType: "application/json",
      body: JSON.stringify({
        detail: {
          error: "owner_decision_resolve_forbidden",
          message: "Nu aveti permisiunea de a rezolva aceasta decizie.",
        },
      }),
    });
  });
  const denyNote = page.locator(`[data-testid="owner-decision-resolve-note-${BLOCKER}"]`);
  await denyNote.fill("incercare operator blocata");
  await page.locator(`[data-testid="owner-decision-resolve-submit-${BLOCKER}"]`).click();
  await page.waitForSelector(`[data-testid="owner-decision-resolve-error-${BLOCKER}"]`, {
    timeout: 10000,
  });
  await page.screenshot({
    path: path.join(outDir, "12_permission_denial_handling.png"),
    fullPage: true,
  });
  console.log("saved 12_permission_denial_handling.png");

  await page.unroute(`**/owner-decisions/${BLOCKER}/resolve`);
  await resetFixture();
  await openExecutionDetails(page);
  await page.getByText("Analiza interna (nu blocheaza productia)").scrollIntoViewIfNeeded();
  await page.screenshot({
    path: path.join(outDir, "13_nonblocking_internal_analysis.png"),
    fullPage: true,
  });
  console.log("saved 13_nonblocking_internal_analysis.png");

  await browser.close();
})();
