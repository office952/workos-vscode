const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require("playwright");

const outDir = path.resolve(
  __dirname,
  "../../docs/qa/product-system-active-path-isolation-v1/mobile_t03_screenshots",
);
const BASE = "http://127.0.0.1:3000";
const ORDER_ID = 23099;

async function capture(page, file, setup) {
  try {
    await setup(page);
    await page.screenshot({ path: path.join(outDir, file), fullPage: true });
    console.log("ok", file);
    return true;
  } catch (err) {
    console.error("fail", file, err.message);
    return false;
  }
}

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

  await capture(page, "01_ready_assigned_task.png", async (p) => {
    await p.goto(`${BASE}/employee-app-v2/tasks`, { waitUntil: "networkidle" });
    await p.waitForSelector('[data-testid="employee-mobile-v2-tasks-list"]');
    const ready = p.locator('[data-testid$="-readiness-badge"]:has-text("Pregătit")').first();
    if (await ready.count()) await ready.scrollIntoViewIfNeeded();
  });

  await capture(page, "02_production_blocked_card.png", async (p) => {
    await p.goto(`${BASE}/employee-app-v2/tasks`, { waitUntil: "networkidle" });
    await p.waitForSelector('[data-testid*="production-badge"]', { timeout: 15000 });
  });

  await capture(page, "03_production_blocker_detail.png", async (p) => {
    await p.goto(
      `${BASE}/employee-app-v2/tasks/node:root_product:TPL-VOLUMETRIC-LETTERS_v2:vector_prep?orderId=${ORDER_ID}`,
      { waitUntil: "networkidle" },
    );
    await p.waitForSelector('[data-testid="employee-mobile-v2-detail-production"]');
  });

  await capture(page, "04_predecessor_file_blocker.png", async (p) => {
    await p.goto(
      `${BASE}/employee-app-v2/tasks/node:root_product:TPL-VOLUMETRIC-LETTERS_v2:cnc_face_cut?orderId=${ORDER_ID}`,
      { waitUntil: "networkidle" },
    );
    await p.waitForSelector('[data-testid="employee-mobile-v2-detail-readiness"]');
  });

  await capture(page, "05_available_not_startable.png", async (p) => {
    await p.goto(`${BASE}/employee-app-v2/tasks`, { waitUntil: "networkidle" });
    await p.waitForSelector('[data-testid="employee-mobile-v2-available-waiting-section"]');
    await p.locator('[data-testid="employee-mobile-v2-available-waiting-section"]').scrollIntoViewIfNeeded();
  });

  await capture(page, "06_in_progress_task.png", async (p) => {
    await p.goto(`${BASE}/employee-app-v2/tasks`, { waitUntil: "networkidle" });
    await p.waitForSelector('[data-testid^="employee-mobile-v2-in-progress-row-"]');
  });

  await capture(page, "07_completed_tasks.png", async (p) => {
    await p.goto(`${BASE}/employee-app-v2/tasks`, { waitUntil: "networkidle" });
    const done = p.locator('[data-testid="employee-mobile-v2-recent-done"]');
    if (await done.count()) await done.scrollIntoViewIfNeeded();
  });

  await capture(page, "08_manager_escalation_detail.png", async (p) => {
    await p.goto(
      `${BASE}/employee-app-v2/tasks/node:root_product:TPL-VOLUMETRIC-LETTERS_v2:vector_prep?orderId=${ORDER_ID}`,
      { waitUntil: "networkidle" },
    );
    await p.waitForSelector('[data-testid="employee-mobile-v2-detail-manager-escalation"]');
  });

  await page.route("**/api/v1/employee-mobile/tasks/truth", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        contract_version: "employee_mobile_task_truth/v1",
        employee_id: 4,
        generated_at: new Date().toISOString(),
        tasks: [
          {
            identity: {
              task_id: "fixture-ready",
              display_label: "Lipire canturi",
            },
            assignment: {
              is_assigned_to_current_employee: true,
              is_available_for_claim: false,
            },
            readiness: {
              is_startable: true,
              readiness_status: "eligible",
              readiness_label: "Eligibil acum",
              production_release_blocked: false,
              can_start: true,
            },
            order_id: ORDER_ID,
            order_code: "ORD-W5INT02-GATE",
            status: "assigned",
          },
        ],
        summary: { total_tasks: 1, assigned_count: 1, available_count: 0, startable_count: 1 },
      }),
    });
  });
  await page.route("**/api/v1/employee-mobile/orders/*/tasks/*", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        task_id: "fixture-ready",
        order_id: ORDER_ID,
        order_code: "ORD-W5INT02-GATE",
        title: "Lipire canturi",
        display_label: "Lipire canturi",
        status: "assigned",
        is_assigned_to_current_employee: true,
        is_startable: true,
        readiness_status: "eligible",
        readiness_label: "Eligibil acum",
        production_release_blocked: false,
      }),
    });
  });
  await capture(page, "09_allowed_comparison_startable.png", async (p) => {
    await p.goto(`${BASE}/employee-app-v2/tasks/fixture-ready?orderId=${ORDER_ID}`, {
      waitUntil: "networkidle",
    });
    await p.waitForSelector('[data-testid="employee-mobile-v2-detail-can-start"]');
    await p.waitForSelector('[data-testid="employee-mobile-v2-detail-readiness-badge"]:has-text("Pregătit")');
  });
  await page.unroute("**/api/v1/employee-mobile/tasks/truth");
  await page.unroute("**/api/v1/employee-mobile/orders/*/tasks/*");

  await capture(page, "10_refresh_stability.png", async (p) => {
    await p.goto(`${BASE}/employee-app-v2/tasks`, { waitUntil: "networkidle" });
    await p.reload({ waitUntil: "networkidle" });
    await p.waitForTimeout(800);
  });

  await page.route("**/api/v1/employee-mobile/tasks/truth", async (route) => {
    await route.fulfill({
      status: 409,
      contentType: "application/json",
      body: JSON.stringify({
        detail: { code: "MOBILE_V2_TASK_ENVELOPE_MISSING", message: "missing envelope" },
      }),
    });
  });
  await capture(page, "11_contract_error_state.png", async (p) => {
    await p.goto(`${BASE}/employee-app-v2/tasks`, { waitUntil: "networkidle" });
    await p.waitForSelector('[data-testid="employee-mobile-v2-tasks-error"]', { timeout: 15000 });
  });
  await page.unroute("**/api/v1/employee-mobile/tasks/truth");

  await page.route("**/api/v1/employee-mobile/tasks/truth", async (route) => {
    await route.fulfill({
      status: 403,
      contentType: "application/json",
      body: JSON.stringify({
        detail: { code: "employee_link_missing", message: "no employee link" },
      }),
    });
  });
  await capture(page, "12_employee_link_error_state.png", async (p) => {
    await p.goto(`${BASE}/employee-app-v2/tasks`, { waitUntil: "networkidle" });
    await p.waitForSelector('[data-testid="employee-mobile-v2-tasks-error"]', { timeout: 15000 });
  });
  await page.unroute("**/api/v1/employee-mobile/tasks/truth");

  await page.route("**/api/v1/employee-mobile/tasks/truth", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        contract_version: "employee_mobile_task_truth/v1",
        employee_id: 4,
        generated_at: new Date().toISOString(),
        tasks: [
          {
            identity: {
              task_id: "fixture-material",
              display_label: "Aplicare folie",
            },
            assignment: {
              is_assigned_to_current_employee: true,
              is_available_for_claim: false,
            },
            readiness: {
              is_startable: false,
              readiness_status: "waiting_material",
              readiness_label: "Așteaptă material",
              material_warning: "Material lipsă: ACM 3mm",
              readiness_reasons: [
                {
                  code: "material_procurement_block",
                  label: "Așteaptă material",
                  message: "ACM 3mm neconfirmat",
                },
              ],
              production_release_blocked: false,
            },
            order_id: ORDER_ID,
            order_code: "ORD-W5INT02-GATE",
            status: "assigned",
          },
        ],
        summary: { total_tasks: 1, assigned_count: 1, available_count: 0 },
      }),
    });
  });
  await capture(page, "13_material_blocker_fixture.png", async (p) => {
    await p.goto(
      `${BASE}/employee-app-v2/tasks/fixture-material?orderId=${ORDER_ID}`,
      { waitUntil: "networkidle" },
    );
    await p.waitForSelector('[data-testid="employee-mobile-v2-detail-materials"]');
  });

  await browser.close();
  console.log("files:", fs.readdirSync(outDir).length, "dir:", outDir);
})();
