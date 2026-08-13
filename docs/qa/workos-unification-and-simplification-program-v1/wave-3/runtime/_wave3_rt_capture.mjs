/**
 * Wave 3 RT — production/execution. READ-ONLY.
 * Never click: generate plan, start/complete/block, assign, machine-run create/start.
 */
import { chromium } from "../../../../../frontend/node_modules/playwright/index.mjs";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const FE = process.env.WORKOS_FE_URL || "http://127.0.0.1:3000";
const OUT = join(__dirname, "screenshots");
const VIEWPORT = { width: 1440, height: 900 };
const KNOWN_EXEC = ["/execution/973024", "/execution/973010"];

const results = [];
const edges = [];
const roleMatrix = [];
const notReached = [];
const orderHandoff = [];
const hoverFocus = [];
const backNav = [];
let seq = 0;

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
  page.setDefaultTimeout(18000);
  await page.goto(`${FE}${path}`, { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForTimeout(1400);
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
function discoverScrollers() {
  return [...document.querySelectorAll("main, nav, [data-testid]")].filter((el) => {
    const oy = getComputedStyle(el).overflowY;
    return (oy === "auto" || oy === "scroll") && el.scrollHeight > el.clientHeight + 2;
  }).map((el) => `${el.getAttribute("data-testid") || el.tagName} max=${el.scrollHeight - el.clientHeight}`);
}

async function exhaust(page, meta) {
  await page.evaluate(setScrollerTop, 0);
  await page.waitForTimeout(100);
  const start = await page.evaluate(scrollerMetrics);
  const nested = await page.evaluate(discoverScrollers);
  const dir = join(OUT, meta.role, meta.theme, slug(meta.route), slug(meta.tab || "default"));
  mkdirSync(dir, { recursive: true });
  const segments = [];
  let idx = 0;
  const step = Math.max(200, start.clientHeight - 48);
  while (idx < 20) {
    const before = await page.evaluate(scrollerMetrics);
    seq += 1;
    const file = `${String(seq).padStart(3, "0")}-s${String(idx).padStart(2, "0")}-y${Math.round(before.scrollTop)}.png`;
    await page.screenshot({ path: join(dir, file) });
    segments.push({
      index: idx,
      scrollTop: before.scrollTop,
      file: `wave-3/runtime/screenshots/${meta.role}/${meta.theme}/${slug(meta.route)}/${slug(meta.tab || "default")}/${file}`,
    });
    if (before.max <= 0 || before.scrollTop >= before.max - 1) break;
    await page.evaluate(setScrollerTop, Math.min(before.max, before.scrollTop + step));
    await page.waitForTimeout(140);
    const after = await page.evaluate(scrollerMetrics);
    if (after.scrollTop <= before.scrollTop + 1) break;
    idx += 1;
  }
  const atMax = await page.evaluate(scrollerMetrics);
  await page.evaluate((m) => {
    const main = document.querySelector("[data-testid='workos-desktop-shell'] main");
    if (main) main.scrollTop = m + 4000;
  }, atMax.max);
  await page.waitForTimeout(100);
  const afterFinal = await page.evaluate(scrollerMetrics);
  const newAfter = afterFinal.scrollTop > atMax.scrollTop + 1 || afterFinal.scrollHeight > atMax.scrollHeight + 2;
  const bottom = afterFinal.max <= 0 || afterFinal.scrollTop >= afterFinal.max - 1;
  const row = {
    ...meta,
    container: start.used,
    SCROLL_START: start.scrollTop,
    SCROLL_END: afterFinal.scrollTop,
    SCROLL_MAX: afterFinal.max,
    BOTTOM_REACHED: bottom ? "YES" : "NO",
    NEW_CONTENT_AFTER_FINAL_SCROLL: newAfter ? "YES" : "NO",
    SCROLL_SEGMENT_COUNT: segments.length,
    FULL_VERTICAL_SCROLL: start.scrollTop === 0 && bottom && !newAfter ? "PASS" : "FAIL",
    NESTED_SCROLL_CONTAINERS: nested,
    segments,
    actualUrl: page.url(),
  };
  results.push(row);
  return row;
}

async function recordRole(page, role, theme, path, expectedAllowed) {
  const url = new URL(page.url());
  const landed = url.pathname;
  const deniedUi = await page.locator("text=/nu ai acces|access denied|nepermis|redirec/i").count();
  const stillOn = landed === path || landed.startsWith(`${path}/`) || (path.includes("/:") && landed.startsWith(path.split("/:")[0]));
  const allowed = stillOn && deniedUi === 0;
  roleMatrix.push({
    role,
    theme,
    route: path,
    ROLE_ALLOWED: allowed ? "YES" : "NO",
    SOURCE: "runtime",
    LANDING: landed,
    EXPECTED: expectedAllowed ? "YES" : "NO",
    MATCH: allowed === expectedAllowed ? "YES" : "NO",
  });
  return allowed;
}

function edge(rec) {
  edges.push({ FOLLOWED: "YES", ...rec });
}

async function expandReadOnly(page) {
  const opened = [];
  const summaries = page.locator("summary");
  const n = Math.min(await summaries.count(), 8);
  for (let i = 0; i < n; i += 1) {
    const s = summaries.nth(i);
    const text = ((await s.innerText()) || "").trim();
    if (/genereaz|start|pornește|finalizeaz|assign|atribuie|salveaz/i.test(text)) continue;
    await s.click().catch(() => {});
    opened.push(text.slice(0, 80));
    await page.waitForTimeout(150);
  }
  return opened;
}

async function capturePath(browser, theme, role, path, expectedAllowed, tab = "default") {
  const { ctx, page } = await openPage(browser, { theme, role, path });
  const allowed = await recordRole(page, role, theme, path, expectedAllowed);
  if (!allowed) {
    notReached.push({
      route: path,
      role,
      theme,
      blocker: `ROLE_ALLOWED=NO landing=${new URL(page.url()).pathname}`,
      SOURCE: "RBAC+runtime",
    });
    seq += 1;
    const dir = join(OUT, role, theme, slug(path), "denied");
    mkdirSync(dir, { recursive: true });
    const file = `${String(seq).padStart(3, "0")}-denied.png`;
    await page.screenshot({ path: join(dir, file) });
    await ctx.close();
    return { page: null, ctx: null, allowed: false };
  }
  await exhaust(page, { role, theme, route: new URL(page.url()).pathname, tab, state: "default" });
  return { page, ctx, allowed: true };
}

async function captureShopFloor(browser, theme, role, expected) {
  const opened = await capturePath(browser, theme, role, "/shop-floor", expected);
  if (!opened.allowed) return;
  const { page, ctx } = opened;
  const blocked = page.getByText(/Blocat|blocked/i).first();
  if (await blocked.count()) {
    await blocked.click().catch(() => {});
    await page.waitForTimeout(300);
    await exhaust(page, { role, theme, route: "/shop-floor", tab: "blocked-focus", state: "board" });
  }
  await ctx.close();
}

async function captureExecutionList(browser, theme, role, expected) {
  const opened = await capturePath(browser, theme, role, "/execution", expected);
  if (!opened.allowed) return null;
  const { page, ctx } = opened;
  const row = page.locator("table tbody tr, [data-testid*='execution'] tr").first();
  let detailPath = null;
  if (await row.count()) {
    await row.click();
    await page.waitForTimeout(900);
    detailPath = new URL(page.url()).pathname;
    if (detailPath.startsWith("/execution/") && detailPath !== "/execution") {
      edge({
        FROM_ROUTE: "/execution",
        CONTROL_LABEL: "execution row",
        ROLE: role,
        TO_ROUTE: detailPath,
        EXPECTED_PURPOSE: "execution plan detail",
        ACTUAL_DESTINATION: detailPath,
        HONESTY_STATUS: /^\/execution\/\d+$/.test(detailPath) ? "GOOD_EDGE" : "SURPRISING_DESTINATION",
      });
      const openedX = await expandReadOnly(page);
      await exhaust(page, {
        role,
        theme,
        route: detailPath,
        tab: "detail",
        state: "execution-detail",
        expandables: openedX,
      });
    }
  }
  await ctx.close();
  return detailPath;
}

async function captureKnownDetail(browser, theme, role) {
  for (const path of KNOWN_EXEC) {
    const { ctx, page } = await openPage(browser, { theme, role, path });
    const dest = new URL(page.url()).pathname;
    const ok = dest === path || dest.startsWith("/execution/");
    if (!ok || dest === "/execution") {
      notReached.push({ route: path, role, theme, blocker: `landed ${dest}` });
      await ctx.close();
      continue;
    }
    await recordRole(page, role, theme, path, true);
    const openedX = await expandReadOnly(page);
    await exhaust(page, { role, theme, route: dest, tab: "known-detail", state: "existing-plan", expandables: openedX });
    const body = await page.locator("body").innerText();
    orderHandoff.push({
      ORDER_ROUTE: "/orders/ORD-IV6-V2-1786318810-31",
      ORDER_ID: dest.includes("973024") ? "973024 / ORD-IV6-V2-1786318810-31" : dest,
      EXECUTION_ENTRY_CONTROL: "direct GET existing",
      DESTINATION: dest,
      ORDER_ID_VISIBLE: /973024|ORD-IV6/i.test(body) ? "YES" : "PARTIAL",
      EXECUTION_PLAN_ID_VISIBLE: /plan\s*#?\s*\d+|execution_plan|plan de execuție/i.test(body) ? "YES" : "UNKNOWN",
      USER_RELEVANCE: "numeric order_id in URL",
      TECHNICAL_LEAK: dest.replace("/execution/", ""),
      HONESTY_STATUS: "TECHNICAL_DESTINATION",
      role,
      theme,
    });
    await ctx.close();
    return dest;
  }
  return null;
}

async function captureMachineRuns(browser, theme, role, expected) {
  const opened = await capturePath(browser, theme, role, "/execution/machine-runs", expected);
  if (!opened.allowed) return;
  const { page, ctx } = opened;
  const all = page.getByRole("button", { name: /Toate|all/i }).first();
  if (await all.count()) {
    await all.click().catch(() => {});
    await page.waitForTimeout(400);
    await exhaust(page, { role, theme, route: "/execution/machine-runs", tab: "scope-all", state: "filtered" });
  }
  const row = page.locator("table tbody tr, a[href*='/execution/machine-runs/']").first();
  if (await row.count()) {
    await row.click();
    await page.waitForTimeout(700);
    const dest = new URL(page.url()).pathname;
    if (/\/execution\/machine-runs\/\d+/.test(dest)) {
      edge({
        FROM_ROUTE: "/execution/machine-runs",
        CONTROL_LABEL: "machine-run row",
        ROLE: role,
        TO_ROUTE: dest,
        HONESTY_STATUS: "GOOD_EDGE",
      });
      await exhaust(page, { role, theme, route: dest, tab: "detail", state: "machine-run-detail" });
    }
  } else {
    notReached.push({
      route: "/execution/machine-runs/:id",
      role,
      theme,
      blocker: "no existing machine-run row",
      MUTATION_REQUIRED: "YES",
      WHY_NOT_FORCED: "would create MachineRun",
    });
  }
  await ctx.close();
}

async function captureSimple(browser, theme, role, path, expected) {
  const opened = await capturePath(browser, theme, role, path, expected);
  if (opened.allowed) await opened.ctx.close();
}

async function captureOrderHandoff(browser, theme, role) {
  const { ctx, page } = await openPage(browser, { theme, role, path: "/orders/ORD-IV6-V2-1786318810-31" });
  await exhaust(page, { role, theme, route: "/orders/ORD-IV6-V2-1786318810-31", tab: "handoff-observe", state: "wave2-order" });
  const viewExec = page.getByRole("button", { name: /Vezi execuția/i }).or(page.getByRole("link", { name: /Vezi execuția/i }));
  const gen = page.getByRole("button", { name: /Generează taskuri producție/i });
  const body = await page.locator("body").innerText();
  const rec = {
    ORDER_ROUTE: "/orders/ORD-IV6-V2-1786318810-31",
    ORDER_ID: "ORD-IV6-V2-1786318810-31",
    EXECUTION_ENTRY_CONTROL: (await viewExec.count()) ? "Vezi execuția" : (await gen.count()) ? "Generează taskuri producție (NOT CLICKED)" : "ABSENT",
    CONTROL_LABEL: (await viewExec.count()) ? await viewExec.first().innerText() : "none-or-generate-only",
    DESTINATION: "",
    CONTEXT_PRESERVED: "UNKNOWN",
    ORDER_ID_VISIBLE: /ORD-IV6/i.test(body) ? "YES" : "NO",
    EXECUTION_PLAN_ID_VISIBLE: /plan/i.test(body) ? "PARTIAL" : "NO",
    USER_RELEVANCE: "order code vs numeric execution id",
    TECHNICAL_LEAK: "dual flux + generate vs view",
    HONESTY_STATUS: "UNKNOWN",
    role,
    theme,
    GENERATE_VISIBLE: (await gen.count()) > 0,
  };
  if (await viewExec.count()) {
    await viewExec.first().click();
    await page.waitForTimeout(1000);
    rec.DESTINATION = new URL(page.url()).pathname;
    rec.CONTEXT_PRESERVED = rec.DESTINATION.startsWith("/execution") ? "PARTIAL" : "NO";
    rec.HONESTY_STATUS = rec.DESTINATION.startsWith("/execution") ? "GOOD_EDGE" : "SURPRISING_DESTINATION";
    edge({
      FROM_ROUTE: "/orders/ORD-IV6-V2-1786318810-31",
      CONTROL_LABEL: "Vezi execuția",
      ROLE: role,
      TO_ROUTE: rec.DESTINATION,
      HONESTY_STATUS: rec.HONESTY_STATUS,
    });
    if (rec.DESTINATION.startsWith("/execution")) {
      await exhaust(page, { role, theme, route: rec.DESTINATION, tab: "from-order", state: "handoff" });
    }
  } else if (await gen.count()) {
    rec.HONESTY_STATUS = "DEAD_END_WITHOUT_MUTATION";
    notReached.push({
      route: "/execution/:id",
      from: rec.ORDER_ROUTE,
      blocker: "only Generează taskuri producție visible — not clicked",
      MUTATION_REQUIRED: "YES",
      WHY_NOT_FORCED: "creates ExecutionPlan",
    });
  }
  orderHandoff.push(rec);
  await ctx.close();
}

async function captureHover(browser, theme) {
  const { ctx, page } = await openPage(browser, { theme, role: "admin", path: "/shop-floor" });
  async function sample(kind, loc) {
    if (!(await loc.count())) {
      hoverFocus.push({ theme, kind, HOVER_STATE: "ABSENT", FOCUS_STATE: "ABSENT" });
      return;
    }
    const el = loc.first();
    await el.scrollIntoViewIfNeeded().catch(() => {});
    await el.hover().catch(() => {});
    await page.waitForTimeout(150);
    seq += 1;
    const dir = join(OUT, "admin", theme, "_shop-floor", "hover-focus");
    mkdirSync(dir, { recursive: true });
    const hf = `${String(seq).padStart(3, "0")}-hover-${kind}.png`;
    await page.screenshot({ path: join(dir, hf) });
    await el.focus().catch(() => {});
    await page.waitForTimeout(150);
    seq += 1;
    const ff = `${String(seq).padStart(3, "0")}-focus-${kind}.png`;
    await page.screenshot({ path: join(dir, ff) });
    const box = await el.evaluate((node) => {
      const s = getComputedStyle(node);
      return { outlineWidth: s.outlineWidth, boxShadow: s.boxShadow };
    });
    hoverFocus.push({
      theme,
      kind,
      HOVER_STATE: "CAPTURED",
      FOCUS_STATE: "CAPTURED",
      VISIBLE_FOCUS: box.outlineWidth !== "0px" || (box.boxShadow && box.boxShadow !== "none") ? "YES" : "WEAK_OR_NONE",
      THEME_PARITY: "PENDING_COMPARE",
    });
  }
  await sample("nav-atelier", page.locator("nav, [data-testid='workos-shell-nav']").getByText("Atelier").first());
  await sample("primary-link", page.getByRole("link").first());
  await page.goto(`${FE}/execution`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(900);
  await sample("exec-row", page.locator("table tbody tr").first());
  await ctx.close();
}

async function captureBack(browser, theme) {
  const { ctx, page } = await openPage(browser, { theme, role: "admin", path: "/execution" });
  const from = new URL(page.url()).pathname;
  const row = page.locator("table tbody tr").first();
  if (await row.count()) {
    await row.click();
    await page.waitForTimeout(800);
    const to = new URL(page.url()).pathname;
    await page.goBack();
    await page.waitForTimeout(700);
    const back = new URL(page.url()).pathname;
    backNav.push({
      FROM_ROUTE: from,
      TO_ROUTE: to,
      BACK_ROUTE: back,
      CONTEXT_PRESERVED: back === "/execution" || back.startsWith("/execution") ? "YES" : "NO",
      theme,
      role: "admin",
    });
  }
  await ctx.close();
}

const browser = await chromium.launch({ headless: true });
try {
  for (const theme of ["light", "dark"]) {
    await captureShopFloor(browser, theme, "admin", true);
    await captureShopFloor(browser, theme, "operator", true);
    await captureShopFloor(browser, theme, "manager", true);
    await captureShopFloor(browser, theme, "sales", false);

    await captureExecutionList(browser, theme, "admin", true);
    await captureExecutionList(browser, theme, "manager", true);
    await captureExecutionList(browser, theme, "sales", true);
    await capturePath(browser, theme, "operator", "/execution", false).then((o) => o.ctx && o.ctx.close());

    if (theme === "light") {
      await captureKnownDetail(browser, theme, "admin");
      await captureOrderHandoff(browser, theme, "admin");
    }

    await captureMachineRuns(browser, theme, "admin", true);
    await captureMachineRuns(browser, theme, "operator", true);
    await capturePath(browser, theme, "sales", "/execution/machine-runs", false).then((o) => o.ctx && o.ctx.close());

    await captureSimple(browser, theme, "admin", "/execution/ops-graph", true);
    await captureSimple(browser, theme, "manager", "/execution/ops-graph", true);
    await captureSimple(browser, theme, "sales", "/execution/ops-graph", false);
    await captureSimple(browser, theme, "operator", "/execution/ops-graph", false);

    await captureSimple(browser, theme, "admin", "/execution/reality-review", true);
    await captureSimple(browser, theme, "manager", "/execution/reality-review", true);

    await captureSimple(browser, theme, "admin", "/operator", true);
    await captureSimple(browser, theme, "operator", "/operator", true);
    await captureSimple(browser, theme, "sales", "/operator", false);

    await captureSimple(browser, theme, "admin", "/tablet", true);
    await captureSimple(browser, theme, "operator", "/tablet", true);

    await captureHover(browser, theme);
    await captureBack(browser, theme);
  }

  const { ctx, page } = await openPage(browser, { theme: "light", role: "admin", path: "/employee-app-v2" });
  seq += 1;
  const dir = join(OUT, "admin", "light", "_employee-app-v2", "observe");
  mkdirSync(dir, { recursive: true });
  const file = `${String(seq).padStart(3, "0")}-observe.png`;
  await page.screenshot({ path: join(dir, file) });
  results.push({
    role: "admin",
    theme: "light",
    route: "/employee-app-v2",
    tab: "observe",
    FULL_VERTICAL_SCROLL: "N/A",
    note: "standalone employee surface — observe only, no task start",
    actualUrl: page.url(),
    segments: [{ file: `wave-3/runtime/screenshots/admin/light/_employee-app-v2/observe/${file}` }],
  });
  edge({
    FROM_ROUTE: "direct",
    CONTROL_LABEL: "URL observe",
    ROLE: "admin",
    TO_ROUTE: new URL(page.url()).pathname,
    HONESTY_STATUS: "TECHNICAL_DESTINATION",
    note: "not in desktop shell nav",
  });
  await ctx.close();
} finally {
  await browser.close();
}

const logPath = join(__dirname, "rt-capture-log.json");
writeFileSync(
  logPath,
  JSON.stringify(
    {
      fe: FE,
      seq,
      surfaces: results.length,
      scrollFail: results.filter((r) => r.FULL_VERTICAL_SCROLL === "FAIL").length,
      results,
      edges,
      roleMatrix,
      orderHandoff,
      hoverFocus,
      backNav,
      notReached,
    },
    null,
    2,
  ),
  "utf8",
);
console.log(
  JSON.stringify(
    {
      surfaces: results.length,
      shots: seq,
      scrollFail: results.filter((r) => r.FULL_VERTICAL_SCROLL === "FAIL").length,
      edges: edges.length,
      roleMatrix: roleMatrix.length,
      orderHandoff: orderHandoff.length,
      notReached: notReached.length,
    },
    null,
    2,
  ),
);
