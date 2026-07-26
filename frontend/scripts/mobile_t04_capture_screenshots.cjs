const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require("playwright");

const outDir = path.resolve(
  __dirname,
  "../../docs/qa/product-system-active-path-isolation-v1/mobile_t04_screenshots",
);
const BASE = "http://127.0.0.1:3000";
const ORDER_ID = 23099;
const VECTOR_PREP = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:vector_prep";
const CNC_FACE = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:cnc_face_cut";

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

function truthBody(tasks) {
  return {
    contract_version: "employee_mobile_task_truth/v1",
    employee_id: 4,
    employee_display_name: "Putaru Sandu",
    generated_at: new Date().toISOString(),
    legacy_mode: false,
    tasks,
    summary: {
      total_tasks: tasks.length,
      assigned_count: tasks.filter((t) => t.assignment?.is_assigned_to_current_employee).length,
      available_count: tasks.filter((t) => t.assignment?.is_available_for_claim).length,
      startable_count: tasks.filter((t) => t.readiness?.can_start || t.readiness?.can_start_from_available).length,
    },
    capabilities: { can_claim_available: true },
  };
}

function assignedTask(id, label, readiness) {
  return {
    identity: { task_id: id, display_label: label },
    assignment: { is_assigned_to_current_employee: true, is_available_for_claim: false },
    readiness,
    order_id: ORDER_ID,
    order_code: "ORD-W5INT02-GATE",
    status: readiness.status || "assigned",
    started_at: readiness.started_at,
  };
}

function availableTask(id, label, readiness) {
  return {
    identity: { task_id: id, display_label: label },
    assignment: {
      is_assigned_to_current_employee: false,
      is_available_for_claim: true,
      can_claim: true,
    },
    readiness,
    order_id: ORDER_ID,
    order_code: "ORD-W5INT02-GATE",
    status: "assigned",
  };
}

function flatFromNested(nested) {
  const r = nested.readiness || {};
  const a = nested.assignment || {};
  return {
    task_id: nested.identity.task_id,
    order_id: nested.order_id,
    order_code: nested.order_code,
    title: nested.identity.display_label,
    display_label: nested.identity.display_label,
    status: nested.status,
    started_at: nested.started_at,
    is_assigned_to_current_employee: a.is_assigned_to_current_employee,
    is_available_for_claim: a.is_available_for_claim,
    can_claim: a.can_claim,
    is_startable: r.is_startable,
    can_start: r.can_start,
    can_start_from_available: r.can_start_from_available,
    readiness_status: r.readiness_status,
    readiness_label: r.readiness_label,
    production_release_blocked: r.production_release_blocked,
    production_blocker_summary: r.production_blocker_summary,
    readiness_reasons: r.readiness_reasons,
    material_warning: r.material_warning,
  };
}

async function routeTruthAndDetail(page, nestedTasks) {
  const flatTasks = nestedTasks.map(flatFromNested);
  await page.route("**/api/v1/employee-mobile/tasks/truth", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(truthBody(nestedTasks)),
    });
  });
  await page.route("**/api/v1/employee-mobile/orders/*/tasks/*", async (route) => {
    const url = route.request().url();
    const match = flatTasks.find((task) => url.includes(encodeURIComponent(task.task_id)));
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(match || flatTasks[0]),
    });
  });
  await page.route("**/api/v1/employee-mobile/orders/*/my-blueprint", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        order_id: ORDER_ID,
        order_label: "ORD-W5INT02-GATE",
        summary: {
          total_tasks: flatTasks.length,
          my_tasks: flatTasks.length,
          my_done: 0,
          overall_progress_percent: 0,
          my_progress_percent: 0,
          blocked: 0,
          in_progress: 0,
        },
        tasks: [],
      }),
    });
  });
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

  const readyAssigned = assignedTask("fixture-start-ready", "Lipire canturi", {
    is_startable: true,
    readiness_status: "eligible",
    readiness_label: "Eligibil acum",
    production_release_blocked: false,
    can_start: true,
  });

  await routeTruthAndDetail(page, [readyAssigned]);
  await capture(page, "01_assigned_ready_start_button.png", async (p) => {
    await p.goto(`${BASE}/employee-app-v2/tasks/fixture-start-ready?orderId=${ORDER_ID}`, {
      waitUntil: "networkidle",
    });
    await p.waitForSelector('[data-testid="employee-mobile-v2-work-room-start"]');
  });
  await page.unroute("**/*");

  const productionBlocked = assignedTask("fixture-production-blocked", "Montaj panou", {
    is_startable: false,
    readiness_status: "eligible",
    readiness_label: "Eligibil acum",
    production_release_blocked: true,
    production_blocker_summary:
      "Productie blocata (OWNER_DECISION_UNRESOLVED). Rezolvare pe desktop.",
    can_start: false,
  });
  await routeTruthAndDetail(page, [productionBlocked]);
  await capture(page, "02_assigned_production_blocked_disabled_start.png", async (p) => {
    await p.goto(
      `${BASE}/employee-app-v2/tasks/fixture-production-blocked?orderId=${ORDER_ID}`,
      { waitUntil: "networkidle" },
    );
    await p.waitForSelector('[data-testid="employee-mobile-v2-work-room-start-blocked"]', {
      timeout: 15000,
    });
  });
  await page.unroute("**/*");

  await capture(page, "03_assigned_readiness_blocked.png", async (p) => {
    await p.goto(
      `${BASE}/employee-app-v2/tasks/${encodeURIComponent(CNC_FACE)}?orderId=${ORDER_ID}`,
      { waitUntil: "networkidle" },
    );
    await p.waitForSelector('[data-testid="employee-mobile-v2-detail-readiness"]', {
      timeout: 15000,
    });
  });

  await routeTruthAndDetail(page, [readyAssigned]);
  await page.route("**/api/v1/employee-mobile/tasks/*/start", async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 1200));
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        status: "ok",
        action: "start",
        task_id: "fixture-start-ready",
        order_id: ORDER_ID,
      }),
    });
  });
  await capture(page, "04_start_pending_state.png", async (p) => {
    await p.goto(`${BASE}/employee-app-v2/tasks/fixture-start-ready?orderId=${ORDER_ID}`, {
      waitUntil: "networkidle",
    });
    const start = p.locator('[data-testid="employee-mobile-v2-work-room-start"]');
    await start.click();
    await p.waitForSelector("text=Se pornește");
  });
  await page.unroute("**/*");

  const inProgressAssigned = assignedTask("fixture-start-ready", "Lipire canturi", {
    is_startable: false,
    readiness_status: "in_progress",
    readiness_label: "În lucru",
    production_release_blocked: false,
    can_start: false,
    status: "in_progress",
    started_at: "2026-07-15T05:00:00+03:00",
  });
  await routeTruthAndDetail(page, [inProgressAssigned]);
  await capture(page, "05_assigned_start_success_in_lucru.png", async (p) => {
    await p.goto(`${BASE}/employee-app-v2/tasks/fixture-start-ready?orderId=${ORDER_ID}`, {
      waitUntil: "networkidle",
    });
    await p.waitForSelector('[data-testid="employee-mobile-v2-detail-readiness-badge"]:has-text("În lucru")');
  });
  await capture(page, "06_active_session_indicator.png", async (p) => {
    await p.waitForSelector('[data-testid="employee-mobile-v2-work-room-status"]');
  });
  await page.unroute("**/*");

  const availableStartable = availableTask("fixture-start-available", "Finisare", {
    is_startable: true,
    readiness_status: "eligible",
    readiness_label: "Eligibil acum",
    production_release_blocked: false,
    can_start: true,
    can_start_from_available: true,
  });
  await routeTruthAndDetail(page, [availableStartable]);
  await capture(page, "07_available_preia_si_porneste.png", async (p) => {
    await p.goto(`${BASE}/employee-app-v2/tasks`, { waitUntil: "networkidle" });
    await p.waitForSelector('[data-testid="employee-mobile-v2-available-start-fixture-start-available"]');
    await p.locator('[data-testid="employee-mobile-v2-available-startable-section"]').scrollIntoViewIfNeeded();
  });
  await page.unroute("**/*");

  await routeTruthAndDetail(page, [availableStartable]);
  await page.route("**/api/v1/employee-mobile/tasks/*/start-from-available", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        status: "ok",
        action: "start",
        task_id: "fixture-start-available",
        order_id: ORDER_ID,
      }),
    });
  });
  await capture(page, "08_available_start_success.png", async (p) => {
    await p.goto(`${BASE}/employee-app-v2/tasks`, { waitUntil: "networkidle" });
    await p.locator('[data-testid="employee-mobile-v2-available-start-fixture-start-available"]').click();
    await p.waitForURL(/fixture-start-available/);
  });
  await page.unroute("**/*");

  await routeTruthAndDetail(page, [inProgressAssigned]);
  await capture(page, "09_task_moved_out_of_disponibile.png", async (p) => {
    await p.goto(`${BASE}/employee-app-v2/tasks`, { waitUntil: "networkidle" });
    await p.waitForSelector('[data-testid="employee-mobile-v2-in-progress-row-fixture-start-ready"]');
  });
  await page.unroute("**/*");

  await routeTruthAndDetail(page, [productionBlocked]);
  await capture(page, "10_structured_production_blocker.png", async (p) => {
    await p.goto(
      `${BASE}/employee-app-v2/tasks/fixture-production-blocked?orderId=${ORDER_ID}`,
      { waitUntil: "networkidle" },
    );
    await p.waitForSelector('[data-testid="employee-mobile-v2-detail-manager-escalation"]');
  });
  await page.unroute("**/*");

  await capture(page, "11_structured_readiness_blocker.png", async (p) => {
    await p.goto(
      `${BASE}/employee-app-v2/tasks/${encodeURIComponent(CNC_FACE)}?orderId=${ORDER_ID}`,
      { waitUntil: "networkidle" },
    );
    await p.waitForSelector('[data-testid="employee-mobile-v2-detail-readiness"]');
  });

  await routeTruthAndDetail(page, [readyAssigned]);
  await page.route("**/api/v1/employee-mobile/tasks/*/start", async (route) => {
    await route.fulfill({
      status: 409,
      contentType: "application/json",
      body: JSON.stringify({
        detail: {
          code: "task_owned_by_other_employee",
          message: "Taskul este deja preluat de alt coleg.",
        },
      }),
    });
  });
  await capture(page, "12_ownership_conflict_error.png", async (p) => {
    await p.goto(`${BASE}/employee-app-v2/tasks/fixture-start-ready?orderId=${ORDER_ID}`, {
      waitUntil: "networkidle",
    });
    await p.locator('[data-testid="employee-mobile-v2-work-room-start"]').click();
    await p.waitForSelector('[data-testid="employee-mobile-v2-work-room-action-error"]');
  });
  await page.unroute("**/*");

  await routeTruthAndDetail(page, [readyAssigned]);
  await page.route("**/api/v1/employee-mobile/tasks/*/start", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        status: "ok",
        action: "start",
        task_id: "fixture-start-ready",
        order_id: ORDER_ID,
        already_started: true,
      }),
    });
  });
  await capture(page, "13_double_tap_stable_state.png", async (p) => {
    await p.goto(`${BASE}/employee-app-v2/tasks/fixture-start-ready?orderId=${ORDER_ID}`, {
      waitUntil: "networkidle",
    });
    const start = p.locator('[data-testid="employee-mobile-v2-work-room-start"]');
    await start.click();
    await start.click({ force: true });
    await p.waitForTimeout(600);
  });
  await page.unroute("**/*");

  await capture(page, "14_refresh_reopen_stability.png", async (p) => {
    await p.goto(`${BASE}/employee-app-v2/tasks`, { waitUntil: "networkidle" });
    await p.reload({ waitUntil: "networkidle" });
    await p.waitForSelector('[data-testid="employee-mobile-v2-tasks-list"]');
  });

  await browser.close();
  console.log("files:", fs.readdirSync(outDir).length, "dir:", outDir);
})();
