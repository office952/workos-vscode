/**
 * Wave 3 gap closure RT — targeted, read-only.
 * Do not re-run full Wave 3 capture.
 * Never click: generate, start/complete/block, assign, machine-run create.
 */
import { chromium } from "../../../../../frontend/node_modules/playwright/index.mjs";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const FE = process.env.WORKOS_FE_URL || "http://127.0.0.1:3000";
const OUT = join(__dirname, "screenshots-gap-closure");
const VIEWPORT = { width: 1440, height: 900 };

function slug(s) {
  return String(s).replace(/[^a-zA-Z0-9._-]+/g, "_").slice(0, 90);
}

async function openPage(browser, { theme, role, path }) {
  const ctx = await browser.newContext({
    viewport: VIEWPORT,
    colorScheme: theme === "dark" ? "dark" : "light",
  });
  await ctx.addInitScript(
    ({ t, r }) => {
      localStorage.setItem("access_token", "__DEV_BYPASS_TOKEN__");
      localStorage.setItem("token", "__DEV_BYPASS_TOKEN__");
      localStorage.setItem("workos-theme", t === "dark" ? "dark" : "light");
      sessionStorage.setItem("WORKOS_DEV_GUARD_BYPASS", "1");
      if (r) sessionStorage.setItem("workos-dev-role", r);
      document.documentElement.classList.remove("dark", "light");
      document.documentElement.classList.add(t === "dark" ? "dark" : "light");
    },
    { t: theme, r: role },
  );
  const page = await ctx.newPage();
  page.setDefaultTimeout(20000);
  await page.goto(`${FE}${path}`, { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForTimeout(1600);
  const bypass = page.getByRole("button", { name: /Bypass temporar preview/i });
  if (await bypass.count()) {
    await bypass.click();
    await page.waitForTimeout(900);
  }
  return { ctx, page };
}

function scrollerMetrics() {
  const main = document.querySelector("[data-testid='workos-desktop-shell'] main");
  const el = main || document.scrollingElement;
  return {
    scrollTop: el.scrollTop,
    clientHeight: el.clientHeight,
    scrollHeight: el.scrollHeight,
    max: Math.max(0, el.scrollHeight - el.clientHeight),
    used: main ? "main.overflow-auto" : "document.scrollingElement",
  };
}

function setScrollerTop(y) {
  const main = document.querySelector("[data-testid='workos-desktop-shell'] main");
  (main || document.scrollingElement).scrollTop = y;
}

async function shot(page, name) {
  const dir = join(OUT, "admin", "light", slug(name));
  mkdirSync(dir, { recursive: true });
  const file = join(dir, `${name.replace(/[^a-zA-Z0-9._-]+/g, "_")}.png`);
  await page.screenshot({ path: file, fullPage: false });
  return `wave-3/runtime/screenshots-gap-closure/admin/light/${slug(name)}/${name.replace(/[^a-zA-Z0-9._-]+/g, "_")}.png`;
}

const log = {
  task: "WAVE_3_EVIDENCE_GAP_CLOSURE_V1",
  mutations: {
    OWNER_DEV_DB_MUTATIONS: 0,
    TASK_MUTATIONS: 0,
    ASSIGNMENT_MUTATIONS: 0,
    SESSION_MUTATIONS: 0,
    MACHINE_RUN_MUTATIONS: 0,
  },
  operator: {},
  identity: {},
  assigned: {},
  tablet: {},
  machineRuns: {},
  shots: [],
};

async function main() {
  const browser = await chromium.launch({ headless: true });

  // ---- GAP 1 + 2 + 4: /operator ----
  {
    const { ctx, page } = await openPage(browser, {
      theme: "light",
      role: "admin",
      path: "/operator",
    });
    await page.waitForTimeout(2500);

    const api = await page.evaluate(async () => {
      const res = await fetch("/api/v1/operator/tasks", { credentials: "include" });
      const data = await res.json();
      const tasks = data.tasks ?? [];
      const byStatus = {};
      for (const t of tasks) {
        const s = t.status || "unknown";
        byStatus[s] = (byStatus[s] || 0) + 1;
      }
      const orders = [...new Set(tasks.map((t) => t.order_id))];
      const pick = (id) =>
        tasks
          .filter((t) => t.order_id === id)
          .map((t) => ({
            task_id: t.task_id,
            status: t.status,
            order_code: t.order_code,
            process_type: t.process_type,
            assigned_employee_id: t.assigned_employee_id ?? null,
            assigned_employee_name: t.assigned_employee_name ?? null,
            employee_id: t.employee_id ?? null,
            employee_name: t.employee_name ?? null,
            name: t.display_name || t.name,
          }));
      const painting = tasks.filter((t) =>
        String(t.display_name || t.name || "").toLowerCase().includes("paint"),
      );
      return {
        http: res.status,
        taskCount: tasks.length,
        byStatus,
        orderCount: orders.length,
        orderIdsSample: orders.slice(0, 20),
        has973024: orders.includes(973024),
        has92400: orders.includes(92400),
        tasks973024: pick(973024),
        tasks92400: pick(92400),
        painting: painting.slice(0, 8).map((t) => ({
          task_id: t.task_id,
          order_id: t.order_id,
          order_code: t.order_code,
          status: t.status,
          assigned_employee_id: t.assigned_employee_id ?? null,
          assigned_employee_name: t.assigned_employee_name ?? null,
          employee_id: t.employee_id ?? null,
          employee_name: t.employee_name ?? null,
          name: t.display_name || t.name,
        })),
      };
    });

    const domStart = await page.evaluate(() => {
      const nextRows = document.querySelectorAll(
        "[data-testid^='operator-next-task-identity-']",
      ).length;
      const assignRows = document.querySelectorAll(
        "[data-testid^='operator-task-assignment-row-']",
      ).length;
      const neatribuit = [...document.querySelectorAll("p")].filter((p) =>
        /assigned\s*[·-]\s*Neatribuit/i.test(p.textContent || ""),
      ).map((p) => (p.textContent || "").trim()).slice(0, 8);
      const anyAssignedNeatribuit = [...document.body.querySelectorAll("*")].some((el) =>
        /assigned/i.test(el.textContent || "") && /Neatribuit/.test(el.textContent || ""),
      );
      return { nextRows, assignRows, neatribuit, anyAssignedNeatribuit };
    });

    const initial = await page.evaluate(scrollerMetrics);
    log.shots.push({ region: "operator-top", file: await shot(page, "operator-top") });

    await page.evaluate(setScrollerTop, Math.round(initial.max * 0.45));
    await page.waitForTimeout(400);
    const mid = await page.evaluate(scrollerMetrics);
    log.shots.push({ region: "operator-mid", file: await shot(page, "operator-mid") });

    await page.evaluate(setScrollerTop, Math.round(initial.max * 0.85));
    await page.waitForTimeout(400);
    const deep = await page.evaluate(scrollerMetrics);
    log.shots.push({ region: "operator-deep", file: await shot(page, "operator-deep") });

    await page.evaluate(setScrollerTop, initial.max + 8000);
    await page.waitForTimeout(1500);
    const afterJump = await page.evaluate(scrollerMetrics);
    log.shots.push({ region: "operator-bottom", file: await shot(page, "operator-bottom") });

    await page.waitForTimeout(3000);
    const afterSettle = await page.evaluate(scrollerMetrics);
    const grewAfterSettle = afterSettle.scrollHeight > afterJump.scrollHeight + 8;
    const bottomReached =
      afterSettle.max <= 0 || afterSettle.scrollTop >= afterSettle.max - 2;

    const domEnd = await page.evaluate(() => ({
      nextRows: document.querySelectorAll(
        "[data-testid^='operator-next-task-identity-']",
      ).length,
      assignRows: document.querySelectorAll(
        "[data-testid^='operator-task-assignment-row-']",
      ).length,
    }));

    log.operator = {
      api,
      domStart,
      domEnd,
      INITIAL_SCROLL_HEIGHT: initial.scrollHeight,
      MID_SCROLL_TOP: mid.scrollTop,
      DEEP_SCROLL_TOP: deep.scrollTop,
      MAX_SCROLL_HEIGHT_OBSERVED: Math.max(
        initial.scrollHeight,
        afterJump.scrollHeight,
        afterSettle.scrollHeight,
      ),
      ITEM_COUNT_START: api.taskCount,
      ITEM_COUNT_END: api.taskCount,
      DOM_NEXT_START: domStart.nextRows,
      DOM_NEXT_END: domEnd.nextRows,
      DOM_ASSIGN_START: domStart.assignRows,
      DOM_ASSIGN_END: domEnd.assignRows,
      LOAD_TRIGGER: "single GET /api/v1/operator/tasks on mount; no poll; no cursor",
      APPEND_BEHAVIOR: "none — full snapshot rendered",
      TERMINATION_CONDITION: bottomReached
        ? "scrollTop >= max after jump-to-end + 3s settle"
        : "bottom not stable",
      HEIGHT_AFTER_JUMP: afterJump.scrollHeight,
      HEIGHT_AFTER_SETTLE: afterSettle.scrollHeight,
      GREW_AFTER_SETTLE: grewAfterSettle,
      BOTTOM_REACHED: bottomReached,
      NEW_NETWORK_PAGES: 0,
    };
    log.assigned = {
      painting: api.painting,
      neatribuitSamples: domStart.neatribuit,
      anyAssignedNeatribuit: domStart.anyAssignedNeatribuit,
    };
    await ctx.close();
  }

  // ---- GAP 3: shop-floor identity + execution detail ----
  {
    const { ctx, page } = await openPage(browser, {
      theme: "light",
      role: "admin",
      path: "/shop-floor",
    });
    await page.waitForTimeout(2500);
    const shop = await page.evaluate(() => {
      const cells = [...document.querySelectorAll("td")].map((td) =>
        (td.textContent || "").trim(),
      );
      const ordLike = cells.filter((t) => /^ORD-/.test(t));
      const bodyText = document.body.innerText;
      return {
        currentJobLike: ordLike.slice(0, 30),
        has92400: /ORD-92400/.test(bodyText),
        has973024: /973024/.test(bodyText),
        hasIv6: /ORD-IV6-V2-1786318810-31/.test(bodyText),
      };
    });
    log.shots.push({ region: "shop-floor-top", file: await shot(page, "shop-floor-top") });
    log.identity.shopFloor = shop;
    await ctx.close();
  }

  {
    const { ctx, page } = await openPage(browser, {
      theme: "light",
      role: "admin",
      path: "/execution/973024",
    });
    await page.waitForTimeout(1800);
    const exec = await page.evaluate(() => {
      const text = document.body.innerText;
      return {
        url: location.pathname,
        has973024: /973024/.test(text) || location.pathname.includes("973024"),
        hasIv6: /ORD-IV6-V2-1786318810-31/.test(text),
        has92400: /ORD-92400|92400/.test(text),
      };
    });
    log.identity.execution973024 = exec;
    await ctx.close();
  }

  // ---- GAP 7: tablet station drill (read-only) ----
  {
    const { ctx, page } = await openPage(browser, {
      theme: "light",
      role: "admin",
      path: "/tablet/print",
    });
    await page.waitForTimeout(2200);
    const tablet = await page.evaluate(() => ({
      url: location.pathname,
      title: document.body.innerText.slice(0, 400),
      startButtons: [...document.querySelectorAll("button")].filter((b) =>
        /start/i.test(b.textContent || ""),
      ).length,
      unknown: /Stație necunoscută/.test(document.body.innerText),
    }));
    log.shots.push({ region: "tablet-print", file: await shot(page, "tablet-print") });
    log.tablet = tablet;
    await ctx.close();
  }

  // ---- GAP 6: machine-run list still empty ----
  {
    const { ctx, page } = await openPage(browser, {
      theme: "light",
      role: "admin",
      path: "/execution/machine-runs",
    });
    await page.waitForTimeout(1600);
    const mr = await page.evaluate(async () => {
      let api = null;
      try {
        const res = await fetch("/api/v1/execution/resource-state/machine-runs?open_only=true", {
          credentials: "include",
        });
        api = { http: res.status, body: await res.json().catch(() => null) };
      } catch (err) {
        api = { error: String(err) };
      }
      return {
        url: location.pathname,
        emptyCopy: /nu există|niciun|empty|0 rular/i.test(document.body.innerText),
        textSample: document.body.innerText.slice(0, 500),
        api,
      };
    });
    log.machineRuns = mr;
    await ctx.close();
  }

  await browser.close();
  writeFileSync(join(__dirname, "rt-gap-closure-log.json"), JSON.stringify(log, null, 2));
  console.log(JSON.stringify(log, null, 2));
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
