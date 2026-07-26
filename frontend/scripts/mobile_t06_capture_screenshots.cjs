const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require("playwright");

const outDir = path.resolve(
  __dirname,
  "../../docs/qa/product-system-active-path-isolation-v1/mobile_t06_screenshots",
);
const BASE = "http://127.0.0.1:3000";
const ORDER_ID = 92400;
const TASK_AVAILABLE = "T-M06-AVAIL";
const TASK_CLAIM_ONLY = "T-M06-CLAIM-ONLY";
const TASK_ASSIGNED = "T-M06-ASSIGNED";
const TASK_OTHER = "T-M06-OTHER";

fs.mkdirSync(outDir, { recursive: true });

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
      startable_count: tasks.filter(
        (t) => t.readiness?.can_start || t.readiness?.can_start_from_available,
      ).length,
    },
    capabilities: { can_claim_available: true },
  };
}

function nestedTask(id, label, { assignment, readiness, status = "assigned" }) {
  return {
    identity: { task_id: id, display_label: label },
    assignment,
    readiness,
    order_id: ORDER_ID,
    order_code: "ORD-T06",
    status,
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
    is_assigned_to_current_employee: a.is_assigned_to_current_employee,
    is_available_for_claim: a.is_available_for_claim,
    can_claim: a.can_claim,
    claimable: a.can_claim,
    assigned_employee_id: a.assigned_employee_id,
    assigned_employee_name: a.assigned_employee_name,
    is_startable: r.is_startable,
    can_start: r.can_start,
    can_start_from_available: r.can_start_from_available,
    can_complete: r.can_complete,
    readiness_status: r.readiness_status,
    readiness_label: r.readiness_label,
    production_release_blocked: r.production_release_blocked,
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
        order_label: "ORD-T06",
        summary: { total_tasks: flatTasks.length, my_tasks: flatTasks.length, my_done: 0 },
        tasks: [],
      }),
    });
  });
}

const availableStartable = nestedTask(TASK_AVAILABLE, "Finisare disponibilă", {
  assignment: {
    is_assigned_to_current_employee: false,
    is_available_for_claim: true,
    can_claim: true,
  },
  readiness: {
    is_startable: true,
    readiness_status: "eligible",
    readiness_label: "Eligibil acum",
    can_start: true,
    can_start_from_available: true,
    can_complete: false,
    production_release_blocked: false,
  },
});

const claimOnly = nestedTask(TASK_CLAIM_ONLY, "Print blocat pregătire", {
  assignment: {
    is_assigned_to_current_employee: false,
    is_available_for_claim: true,
    can_claim: true,
  },
  readiness: {
    is_startable: false,
    readiness_status: "waiting_predecessor",
    readiness_label: "Așteaptă task anterior",
    can_start: false,
    can_start_from_available: false,
    can_complete: false,
    production_release_blocked: false,
  },
});

const assignedMine = nestedTask(TASK_ASSIGNED, "Lipire canturi", {
  assignment: {
    assigned_employee_id: 4,
    assigned_employee_name: "Putaru Sandu",
    is_assigned_to_current_employee: true,
    is_available_for_claim: false,
    can_claim: false,
  },
  readiness: {
    is_startable: true,
    readiness_status: "eligible",
    readiness_label: "Eligibil acum",
    can_start: true,
    can_complete: false,
    production_release_blocked: false,
  },
});

const assignedOther = nestedTask(TASK_OTHER, "Montaj panou", {
  assignment: {
    assigned_employee_id: 99,
    assigned_employee_name: "Alt coleg",
    is_assigned_to_current_employee: false,
    is_available_for_claim: false,
    can_claim: false,
  },
  readiness: {
    is_startable: false,
    readiness_status: "assigned_other",
    readiness_label: "Atribuit altui coleg",
    can_start: false,
    can_complete: false,
    production_release_blocked: false,
  },
});

const inProgressMine = nestedTask(TASK_ASSIGNED, "Lipire canturi", {
  assignment: {
    assigned_employee_id: 4,
    assigned_employee_name: "Putaru Sandu",
    is_assigned_to_current_employee: true,
    is_available_for_claim: false,
    can_claim: false,
  },
  readiness: {
    is_startable: false,
    readiness_status: "in_progress",
    readiness_label: "În lucru",
    can_start: false,
    can_complete: true,
    production_release_blocked: false,
  },
  status: "in_progress",
});

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 390, height: 844 },
    isMobile: true,
    hasTouch: true,
  });
  await context.addInitScript(() => sessionStorage.setItem("WORKOS_DEV_GUARD_BYPASS", "1"));
  const page = await context.newPage();
  let ok = 0;

  await routeTruthAndDetail(page, [availableStartable]);
  ok += await capture(page, "01_available_claimable_task.png", async (p) => {
    await p.goto(`${BASE}/employee-app-v2/tasks`, { waitUntil: "networkidle" });
    await p.waitForSelector('[data-testid="employee-mobile-v2-available-tasks"]');
  });

  ok += await capture(page, "02_primary_preia_si_porneste.png", async (p) => {
    await p.goto(`${BASE}/employee-app-v2/tasks/${TASK_AVAILABLE}?orderId=${ORDER_ID}`, {
      waitUntil: "networkidle",
    });
    await p.waitForSelector('[data-testid="employee-mobile-v2-work-room-start"]');
  });

  await page.unroute("**/*");
  await routeTruthAndDetail(page, [claimOnly]);
  ok += await capture(page, "03_secondary_claim_only_action.png", async (p) => {
    await p.goto(`${BASE}/employee-app-v2/tasks/${TASK_CLAIM_ONLY}?orderId=${ORDER_ID}`, {
      waitUntil: "networkidle",
    });
    await p.waitForSelector('[data-testid="employee-mobile-v2-work-room-claim"]');
  });

  await page.route("**/api/v1/employee-mobile/tasks/*/claim", async (route) => {
    await new Promise((r) => setTimeout(r, 900));
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        status: "ok",
        action: "claim",
        task_id: TASK_CLAIM_ONLY,
        order_id: ORDER_ID,
        assigned_employee_id: 4,
        already_claimed: false,
      }),
    });
  });
  ok += await capture(page, "04_claim_pending.png", async (p) => {
    await p.goto(`${BASE}/employee-app-v2/tasks/${TASK_CLAIM_ONLY}?orderId=${ORDER_ID}`, {
      waitUntil: "networkidle",
    });
    await p.locator('[data-testid="employee-mobile-v2-work-room-claim"]').click();
    await p.waitForSelector("text=Se preia");
  });

  await page.unroute("**/*");
  await routeTruthAndDetail(page, [assignedMine]);
  ok += await capture(page, "05_claim_success_moved_to_my_tasks.png", async (p) => {
    await p.goto(`${BASE}/employee-app-v2/tasks`, { waitUntil: "networkidle" });
    await p.waitForSelector('[data-testid="employee-mobile-v2-assigned-section"]');
  });

  await page.unroute("**/*");
  let holdTruthReload = false;
  const flatAvailable = [availableStartable].map(flatFromNested);
  await page.route("**/api/v1/employee-mobile/tasks/truth", async (route) => {
    if (holdTruthReload) {
      await new Promise((r) => setTimeout(r, 1800));
      holdTruthReload = false;
    }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(truthBody([availableStartable])),
    });
  });
  await page.route("**/api/v1/employee-mobile/orders/*/tasks/*", async (route) => {
    const url = route.request().url();
    const match = flatAvailable.find((task) => url.includes(encodeURIComponent(task.task_id)));
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(match || flatAvailable[0]),
    });
  });
  await page.route("**/api/v1/employee-mobile/orders/*/my-blueprint", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        order_id: ORDER_ID,
        order_label: "ORD-T06",
        summary: { total_tasks: 1, my_tasks: 1, my_done: 0 },
        tasks: [],
      }),
    });
  });
  await page.route("**/api/v1/employee-mobile/tasks/*/start-from-available", async (route) => {
    holdTruthReload = true;
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        status: "ok",
        action: "start",
        task_id: TASK_AVAILABLE,
        order_id: ORDER_ID,
        timestamp: new Date().toISOString(),
      }),
    });
  });
  ok += await capture(page, "06_start_from_available_success.png", async (p) => {
    await p.goto(`${BASE}/employee-app-v2/tasks/${TASK_AVAILABLE}?orderId=${ORDER_ID}`, {
      waitUntil: "networkidle",
    });
    await p.locator('[data-testid="employee-mobile-v2-work-room-start"]').click();
    await p.waitForSelector('[data-testid="employee-mobile-v2-work-room-action-success"]');
  });

  await page.unroute("**/*");
  await routeTruthAndDetail(page, [{ ...inProgressMine, started_at: new Date().toISOString() }]);
  ok += await capture(page, "07_in_lucru_after_atomic_start.png", async (p) => {
    await p.goto(`${BASE}/employee-app-v2/tasks/${TASK_ASSIGNED}?orderId=${ORDER_ID}`, {
      waitUntil: "networkidle",
    });
    await p.waitForSelector('[data-testid="employee-mobile-v2-active-session"]');
  });

  await page.unroute("**/*");
  await routeTruthAndDetail(page, [availableStartable]);
  await page.route("**/api/v1/employee-mobile/tasks/*/start-from-available", async (route) => {
    await route.fulfill({
      status: 409,
      contentType: "application/json",
      body: JSON.stringify({
        detail: {
          error: "task_already_assigned",
          message: "Taskul este deja preluat de alt coleg.",
        },
      }),
    });
  });
  ok += await capture(page, "08_assignment_conflict.png", async (p) => {
    await p.goto(`${BASE}/employee-app-v2/tasks/${TASK_AVAILABLE}?orderId=${ORDER_ID}`, {
      waitUntil: "networkidle",
    });
    await p.locator('[data-testid="employee-mobile-v2-work-room-start"]').click();
    await p.waitForSelector('[data-testid="employee-mobile-v2-work-room-action-error"]');
  });

  await page.unroute("**/*");
  await routeTruthAndDetail(page, [assignedOther]);
  ok += await capture(page, "09_task_assigned_to_another_employee.png", async (p) => {
    await p.goto(`${BASE}/employee-app-v2/tasks/${TASK_OTHER}?orderId=${ORDER_ID}`, {
      waitUntil: "networkidle",
    });
    await p.waitForSelector('[data-testid="employee-mobile-v2-work-room"]');
  });

  await page.unroute("**/*");
  await routeTruthAndDetail(page, [assignedMine]);
  ok += await capture(page, "10_manager_assigned_task_visible.png", async (p) => {
    await p.goto(`${BASE}/employee-app-v2/tasks`, { waitUntil: "networkidle" });
    await p.waitForSelector(`[data-testid="employee-mobile-v2-task-row-${TASK_ASSIGNED}"]`);
  });

  await browser.close();
  console.log(`Captured ${ok} screenshots in ${outDir}`);
  process.exit(ok >= 10 ? 0 : 1);
})();
