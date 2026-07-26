/**
 * W6-INT-02 integration gate screenshots — full Wave 6 desktop flow.
 */
const { chromium } = require("playwright");
const path = require("node:path");
const { execSync } = require("node:child_process");
const fs = require("node:fs");

const outDir = path.resolve(
  __dirname,
  "../../docs/qa/product-system-active-path-isolation-v1/w6_int_02_screenshots",
);
const BASE = "http://127.0.0.1:3000";
const API = "http://127.0.0.1:8001";
const BLOCKED = 23150;
const ALLOWED = 23099;
const BLOCKER = "INTERNAL_SABLON_FOREX_COST";
const PYTHON = path.resolve(__dirname, "../.venv/Scripts/python.exe");
const DEV_HEADERS = {
  Authorization: "Bearer __DEV_BYPASS_TOKEN__",
  Origin: "http://127.0.0.1:3000",
  "Content-Type": "application/json",
};

function resetFixture() {
  execSync(`"${PYTHON}" scripts/w6_t03_blocked_fixture_setup.py`, {
    cwd: path.resolve(__dirname, ".."),
    stdio: "pipe",
    env: {
      ...process.env,
      APP_ENV: "development",
      ENVIRONMENT: "development",
      DATABASE_URL: "sqlite+aiosqlite:///./dev.db",
      JWT_SECRET_KEY: "local-dev-secret-not-for-production",
    },
  });
}

async function resolveApi(code, note) {
  const res = await fetch(
    `${API}/api/v1/execution/orders/${BLOCKED}/owner-decisions/${code}/resolve`,
    { method: "POST", headers: DEV_HEADERS, body: JSON.stringify({ status: "resolved", note }) },
  );
  return res.json();
}

async function openExecution(page) {
  await page.goto(`${BASE}/execution/${BLOCKED}`, { waitUntil: "networkidle" });
  await page.waitForSelector('[data-testid="operator-production-release-summary"]', { timeout: 60000 });
  await page.getByTestId("operator-production-release-details-toggle").click();
  await page.waitForSelector('[data-testid="operator-owner-decision-details"]', { timeout: 15000 });
}

async function openOperator(page) {
  await page.goto(`${BASE}/operator?orderId=${BLOCKED}`, { waitUntil: "networkidle" });
  await page.waitForSelector('[data-testid="operator-production-release-status"]', { timeout: 60000 });
  await page.getByTestId("operator-production-release-details-toggle").click().catch(() => {});
}

(async () => {
  fs.mkdirSync(outDir, { recursive: true });
  resetFixture();

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  await context.addInitScript(() => sessionStorage.setItem("WORKOS_DEV_GUARD_BYPASS", "1"));
  const page = await context.newPage();

  await openExecution(page);
  await page.screenshot({ path: path.join(outDir, "01_blocked_strip_three_blockers.png"), fullPage: true });
  console.log("01");

  await page.getByText("Blocat pentru productie").first().scrollIntoViewIfNeeded().catch(() => {});
  await page.screenshot({ path: path.join(outDir, "02_component_aware_task_rows.png"), fullPage: true });
  console.log("02");

  await page.getByTestId("operator-production-release-details-toggle").click();
  await page.waitForSelector(`[data-testid="owner-decision-resolve-form-${BLOCKER}"]`, { timeout: 15000 });
  await page.getByTestId(`owner-decision-resolve-form-${BLOCKER}`).scrollIntoViewIfNeeded();
  await page.screenshot({ path: path.join(outDir, "03_manager_resolve_action_visible.png"), fullPage: true });
  console.log("03");

  await openOperator(page);
  await page.screenshot({ path: path.join(outDir, "04_operator_no_resolve_action.png"), fullPage: true });
  console.log("04");

  await openExecution(page);
  const note = page.locator(`[data-testid="owner-decision-resolve-note-${BLOCKER}"]`);
  await note.fill("ab");
  await page.locator(`[data-testid="owner-decision-resolve-submit-${BLOCKER}"]`).click().catch(() => {});
  await page.screenshot({ path: path.join(outDir, "05_invalid_note_submit_disabled.png"), fullPage: true });
  console.log("05");

  await note.fill("W6-INT-02 gate: prima rezolvare partiala.");
  await page.locator(`[data-testid="owner-decision-resolve-submit-${BLOCKER}"]`).click();
  await page.waitForTimeout(2000);
  await page.screenshot({ path: path.join(outDir, "06_after_one_blocker_resolved.png"), fullPage: true });
  console.log("06");

  await page.getByTestId("operator-production-blocker-count").scrollIntoViewIfNeeded();
  await page.screenshot({ path: path.join(outDir, "07_still_blocked_two_remaining.png"), fullPage: true });
  console.log("07");

  await resolveApi("INTERNAL_MONTAJ_RULE", "W6-INT-02: Montaj rezolvat.");
  await resolveApi("INTERNAL_CONSUMABLES_RULE", "W6-INT-02: Consumabile rezolvat.");
  await page.reload({ waitUntil: "networkidle" });
  await page.getByTestId("operator-production-release-details-toggle").click();
  await page.waitForTimeout(800);
  await page.screenshot({ path: path.join(outDir, "08_all_blockers_resolved.png"), fullPage: true });
  console.log("08");

  await page.getByTestId("operator-production-release-status").scrollIntoViewIfNeeded();
  await page.screenshot({ path: path.join(outDir, "09_production_allowed_after_refresh.png"), fullPage: true });
  console.log("09");

  await page.getByText("Blocat pentru productie").first().scrollIntoViewIfNeeded().catch(() => {});
  await page.screenshot({ path: path.join(outDir, "10_task_startability_updated.png"), fullPage: true });
  console.log("10");

  await page.getByText("Rezolvat de:").first().scrollIntoViewIfNeeded();
  await page.screenshot({ path: path.join(outDir, "11_resolver_timestamp_metadata.png"), fullPage: true });
  console.log("11");

  await openOperator(page);
  await page.screenshot({ path: path.join(outDir, "12_operator_view_updated_state.png"), fullPage: true });
  console.log("12");

  await page.goto(`${BASE}/execution/${ALLOWED}`, { waitUntil: "networkidle" });
  await page.waitForSelector('[data-testid="operator-production-release-summary"]', { timeout: 60000 });
  await page.screenshot({ path: path.join(outDir, "13_allowed_comparison_23099.png"), fullPage: true });
  console.log("13");

  resetFixture();
  const hashRes = await fetch(`${API}/api/v1/operator/orders/${BLOCKED}/task-truth`, { headers: DEV_HEADERS });
  const truth = await hashRes.json();
  await openExecution(page);
  await page.getByTestId(`owner-decision-code-${BLOCKER}`).scrollIntoViewIfNeeded();
  await page.screenshot({ path: path.join(outDir, "14_frozen_identity_codes_unchanged.png"), fullPage: true });
  console.log("14 frozen codes, contract:", truth.contract_version);

  await resolveApi(BLOCKER, "W6-INT-02 idempotent probe.");
  await openExecution(page);
  await page.waitForSelector(`[data-testid="owner-decision-resolved-state-${BLOCKER}"]`, { timeout: 15000 });
  await page.screenshot({ path: path.join(outDir, "15_idempotent_resolved_state.png"), fullPage: true });
  console.log("15");

  resetFixture();
  await openExecution(page);
  await page.route(`**/owner-decisions/${BLOCKER}/resolve`, async (route) => {
    await route.fulfill({
      status: 403,
      contentType: "application/json",
      body: JSON.stringify({
        detail: { error: "owner_decision_resolve_forbidden", message: "Nu aveti permisiunea." },
      }),
    });
  });
  await page.locator(`[data-testid="owner-decision-resolve-note-${BLOCKER}"]`).fill("incercare blocata");
  await page.locator(`[data-testid="owner-decision-resolve-submit-${BLOCKER}"]`).click();
  await page.waitForSelector(`[data-testid="owner-decision-resolve-error-${BLOCKER}"]`, { timeout: 10000 });
  await page.screenshot({ path: path.join(outDir, "16_permission_denied_handling.png"), fullPage: true });
  console.log("16");

  await browser.close();
})();
