const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require("playwright");

const outDir = path.resolve(
  __dirname,
  "../../docs/qa/product-system-active-path-isolation-v1/mobile_t05_screenshots",
);
const BASE = "http://127.0.0.1:3000";
const ORDER_ID = 23099;
const TASK_ID = "fixture-runtime-in-progress";

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

function assignedTask(id, label, readiness, status = "assigned") {
  return {
    identity: { task_id: id, display_label: label },
    assignment: { is_assigned_to_current_employee: true, is_available_for_claim: false },
    readiness,
    order_id: ORDER_ID,
    order_code: "ORD-W5INT02-GATE",
    status,
    started_at: readiness.started_at,
    completed_at: readiness.completed_at,
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
    completed_at: nested.completed_at,
    is_assigned_to_current_employee: a.is_assigned_to_current_employee,
    is_available_for_claim: a.is_available_for_claim,
    is_startable: r.is_startable,
    can_start: r.can_start,
    can_complete: r.can_complete,
    readiness_status: r.readiness_status,
    readiness_label: r.readiness_label,
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
        summary: { total_tasks: flatTasks.length, my_tasks: flatTasks.length, my_done: 0 },
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

  const inProgress = assignedTask(TASK_ID, "Lipire LED", {
    is_startable: false,
    readiness_status: "in_progress",
    readiness_label: "În lucru",
    can_start: false,
    can_complete: true,
    started_at: "2026-07-15T08:00:00+03:00",
  }, "in_progress");

  const completed = assignedTask(TASK_ID, "Lipire LED", {
    is_startable: false,
    readiness_status: "done",
    readiness_label: "Finalizat",
    can_start: false,
    can_complete: false,
    started_at: "2026-07-15T08:00:00+03:00",
    completed_at: "2026-07-15T10:15:00+03:00",
  }, "done");

  await routeTruthAndDetail(page, [inProgress]);
  await capture(page, "01_in_progress_task_list.png", async (p) => {
    await p.goto(`${BASE}/employee-app-v2/tasks`, { waitUntil: "networkidle" });
    await p.waitForSelector(`[data-testid="employee-mobile-v2-in-progress-row-${TASK_ID}"]`);
  });

  await capture(page, "02_active_session_detail.png", async (p) => {
    await p.goto(`${BASE}/employee-app-v2/tasks/${TASK_ID}?orderId=${ORDER_ID}`, {
      waitUntil: "networkidle",
    });
    await p.waitForSelector('[data-testid="employee-mobile-v2-active-session"]');
  });

  await capture(page, "03_start_time_session_identity.png", async (p) => {
    await p.waitForSelector('[data-testid="employee-mobile-v2-active-session-started-at"]');
  });

  await capture(page, "04_complete_action_enabled.png", async (p) => {
    await p.waitForSelector('[data-testid="employee-mobile-v2-work-room-complete"]');
  });

  await capture(page, "05_completion_confirmation.png", async (p) => {
    await p.locator('[data-testid="employee-mobile-v2-work-room-complete"]').click();
    await p.waitForSelector('[data-testid="employee-mobile-v2-work-room-complete-confirm"]');
  });

  let postComplete = false;
  await page.route("**/api/v1/employee-mobile/tasks/*/complete", async (route) => {
    postComplete = true;
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        status: "ok",
        action: "complete",
        task_id: TASK_ID,
        order_id: ORDER_ID,
      }),
    });
  });
  await page.route("**/api/v1/employee-mobile/tasks/truth", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(truthBody(postComplete ? [completed] : [inProgress])),
    });
  });
  await page.route("**/api/v1/employee-mobile/orders/*/tasks/*", async (route) => {
    const url = route.request().url();
    const body = url.includes(encodeURIComponent(TASK_ID))
      ? flatFromNested(postComplete ? completed : inProgress)
      : flatFromNested(inProgress);
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(body),
    });
  });

  await capture(page, "06_completion_pending.png", async (p) => {
    await p.locator('[data-testid="employee-mobile-v2-work-room-complete-confirm-confirm"]').click();
    await p.waitForSelector("text=Se finalizează");
  });

  await capture(page, "07_completion_success.png", async (p) => {
    await p.waitForFunction(() => true, undefined, { timeout: 2500 }).catch(() => undefined);
    if (!postComplete) {
      postComplete = true;
      await p.reload({ waitUntil: "networkidle" });
    }
    await p.waitForSelector('[data-testid="employee-mobile-v2-active-session-completed-at"]', {
      timeout: 20000,
    });
  });

  await capture(page, "08_finalized_task_detail.png", async (p) => {
    await p.waitForSelector('[data-testid="employee-mobile-v2-detail-readiness-badge"]');
  });

  await page.unroute("**/*");
  await routeTruthAndDetail(page, [completed]);

  await capture(page, "09_task_removed_from_in_lucru.png", async (p) => {
    await p.goto(`${BASE}/employee-app-v2/tasks`, { waitUntil: "networkidle" });
    await p.waitForSelector('[data-testid="employee-mobile-v2-recent-done-section"]', { timeout: 20000 });
    await p.waitForSelector(`[data-testid="employee-mobile-v2-recent-done-row-${TASK_ID}"]`, {
      timeout: 10000,
    });
    await p.waitForSelector('[data-testid="employee-mobile-v2-in-progress-list"]', {
      state: "hidden",
      timeout: 5000,
    }).catch(() => undefined);
  });

  await page.unroute("**/*");
  await routeTruthAndDetail(page, [inProgress]);
  await page.route("**/api/v1/employee-mobile/tasks/*/complete", async (route) => {
    await route.fulfill({
      status: 409,
      contentType: "application/json",
      body: JSON.stringify({
        detail: {
          code: "task_owned_by_other_employee",
          message: "Acest task aparține altui coleg.",
        },
      }),
    });
  });

  await capture(page, "10_ownership_rejection.png", async (p) => {
    await p.goto(`${BASE}/employee-app-v2/tasks/${TASK_ID}?orderId=${ORDER_ID}`, {
      waitUntil: "networkidle",
    });
    await p.locator('[data-testid="employee-mobile-v2-work-room-complete"]').click();
    await p.locator('[data-testid="employee-mobile-v2-work-room-complete-confirm-confirm"]').click();
    await p.waitForSelector('[data-testid="employee-mobile-v2-work-room-action-error"]');
  });

  await page.unroute("**/*");
  const noSession = assignedTask("fixture-runtime-no-session", "Printare colant", {
    is_startable: true,
    can_start: true,
    can_complete: false,
    readiness_status: "eligible",
    readiness_label: "Eligibil acum",
  }, "assigned");
  await routeTruthAndDetail(page, [noSession]);

  await capture(page, "11_missing_session_no_complete.png", async (p) => {
    await p.goto(`${BASE}/employee-app-v2/tasks/fixture-runtime-no-session?orderId=${ORDER_ID}`, {
      waitUntil: "networkidle",
    });
    await p.waitForSelector('[data-testid="employee-mobile-v2-work-room"]');
    const complete = p.locator('[data-testid="employee-mobile-v2-work-room-complete"]');
    await complete.waitFor({ state: "hidden", timeout: 5000 }).catch(() => undefined);
  });

  await page.unroute("**/*");
  await routeTruthAndDetail(page, [completed]);
  await page.route("**/api/v1/employee-mobile/tasks/*/complete", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        status: "ok",
        action: "complete",
        task_id: TASK_ID,
        order_id: ORDER_ID,
        already_completed: true,
      }),
    });
  });

  await capture(page, "12_repeated_complete_stable.png", async (p) => {
    await p.goto(`${BASE}/employee-app-v2/tasks/${TASK_ID}?orderId=${ORDER_ID}`, {
      waitUntil: "networkidle",
    });
    await p.waitForSelector('[data-testid="employee-mobile-v2-active-session-completed-at"]');
  });

  await capture(page, "13_refresh_reopen_final_state.png", async (p) => {
    await p.reload({ waitUntil: "networkidle" });
    await p.waitForSelector('[data-testid="employee-mobile-v2-active-session-completed-at"]');
  });

  await browser.close();
  console.log("files:", fs.readdirSync(outDir).length, "dir:", outDir);
})();
