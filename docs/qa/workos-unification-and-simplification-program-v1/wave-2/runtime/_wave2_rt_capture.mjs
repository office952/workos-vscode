/**
 * Wave 2 RT capture — commercial spine. Read-only. No create/handoff/convert.
 * Primary scroller: main.overflow-auto. Do not open /intake-v6/operator (bootstraps).
 */
import { chromium } from "../../../../../frontend/node_modules/playwright/index.mjs";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const FE = process.env.WORKOS_FE_URL || "http://127.0.0.1:3000";
const OUT = join(__dirname, "screenshots");
const VIEWPORT = { width: 1440, height: 900 };
const KNOWN_V6 = [
  "a1598742-ccb8-4228-b401-a255cd2bfe4f",
  "IV6-F823AA06",
  "ce8f2b4e-de60-4cd7-9dc8-7a66ccc5853f",
];

const results = [];
const edges = [];
const notReached = [];
let seq = 0;

function slug(s) {
  return String(s).replace(/[^a-zA-Z0-9._-]+/g, "_").slice(0, 80);
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
    await page.waitForTimeout(1000);
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
  const el = main || document.scrollingElement;
  el.scrollTop = y;
}

function discoverScrollers() {
  return [...document.querySelectorAll("main, nav, [data-testid]")].filter((el) => {
    const oy = getComputedStyle(el).overflowY;
    return (oy === "auto" || oy === "scroll") && el.scrollHeight > el.clientHeight + 2;
  }).map((el) => `${el.getAttribute("data-testid") || el.tagName} max=${el.scrollHeight - el.clientHeight}`);
}

async function exhaust(page, meta) {
  await page.evaluate(setScrollerTop, 0);
  await page.waitForTimeout(120);
  const start = await page.evaluate(scrollerMetrics);
  const nested = await page.evaluate(discoverScrollers);
  const dir = join(OUT, meta.role, meta.theme, slug(meta.route), slug(meta.tab || "default"));
  mkdirSync(dir, { recursive: true });
  const segments = [];
  let idx = 0;
  const step = Math.max(200, start.clientHeight - 48);
  while (idx < 24) {
    const before = await page.evaluate(scrollerMetrics);
    seq += 1;
    const file = `${String(seq).padStart(3, "0")}-s${String(idx).padStart(2, "0")}-y${Math.round(before.scrollTop)}.png`;
    await page.screenshot({ path: join(dir, file) });
    segments.push({
      index: idx,
      scrollTop: before.scrollTop,
      file: `wave-2/runtime/screenshots/${meta.role}/${meta.theme}/${slug(meta.route)}/${slug(meta.tab || "default")}/${file}`,
    });
    if (before.max <= 0 || before.scrollTop >= before.max - 1) break;
    await page.evaluate(setScrollerTop, Math.min(before.max, before.scrollTop + step));
    await page.waitForTimeout(160);
    const after = await page.evaluate(scrollerMetrics);
    if (after.scrollTop <= before.scrollTop + 1) break;
    idx += 1;
  }
  const atMax = await page.evaluate(scrollerMetrics);
  await page.evaluate((m) => {
    const main = document.querySelector("[data-testid='workos-desktop-shell'] main");
    if (main) main.scrollTop = m + 4000;
  }, atMax.max);
  await page.waitForTimeout(120);
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

function edge(rec) {
  edges.push({ FOLLOWED: "YES", ...rec });
}

const browser = await chromium.launch({ headless: true });

async function captureIntake(theme, role) {
  const { ctx, page } = await openPage(browser, { theme, role, path: "/intake" });
  await exhaust(page, { role, theme, route: "/intake", tab: "default", state: "list" });
  const tech = page.getByTestId("work-intake-technical-details");
  if (await tech.count()) {
    await tech.first().click();
    await page.waitForTimeout(250);
    await exhaust(page, { role, theme, route: "/intake", tab: "technical-details", expandable: "work-intake-technical-details" });
  }
  const row = page.locator("[data-testid^='work-intake-row-']").first();
  if (await row.count()) {
    await row.click();
    await page.waitForTimeout(500);
    await exhaust(page, { role, theme, route: "/intake", tab: "row-selected", state: "detail-panel" });
    const edit = page.getByTestId("work-intake-primary-edit");
    if (await edit.count()) {
      const hrefHint = await edit.getAttribute("href");
      await edit.click();
      await page.waitForTimeout(1500);
      const dest = new URL(page.url()).pathname;
      edge({
        FROM_ROUTE: "/intake",
        FROM_ELEMENT: "work-intake-primary-edit",
        CONTROL_LABEL: "Deschide Intake V6",
        ROLE: role,
        TO_ROUTE: dest,
        ACTUAL_DESTINATION: dest,
        EXPECTED_PURPOSE: "open existing V6 workspace",
        HONESTY_STATUS: dest.includes("/intake-v6/") ? "GOOD_EDGE" : "SURPRISING_DESTINATION",
      });
      if (dest.includes("/intake-v6/") && !dest.endsWith("/intake-v6/operator") && dest !== "/intake-v6/operator") {
        await captureV6OnPage(page, theme, role, dest);
      } else {
        notReached.push({ route: "/intake-v6/:id/operator", blocker: `edit landed on ${dest}` });
      }
    }
  } else {
    notReached.push({ route: "/intake", state: "row-selected", blocker: "no work-intake-row-* in list" });
    for (const id of KNOWN_V6) {
      const { ctx: c2, page: p2 } = await openPage(browser, {
        theme,
        role,
        path: `/intake-v6/${id}/operator`,
      });
      const dest = new URL(p2.url()).pathname;
      if (dest.includes(id) || dest.includes("intake-v6")) {
        await captureV6OnPage(p2, theme, role, dest);
        await c2.close();
        break;
      }
      await c2.close();
    }
  }
  await ctx.close();
}

async function captureV6OnPage(page, theme, role, route) {
  await page.waitForTimeout(800);
  await exhaust(page, { role, theme, route, tab: "layers", state: "v6-step" });
  for (const step of ["review", "confirm"]) {
    const btn = page.getByTestId(`intake-v6-progress-step-${step}`);
    if (!(await btn.count())) continue;
    const disabled = await btn.isDisabled().catch(() => false);
    if (disabled) {
      notReached.push({ route, tab: step, blocker: "step button disabled — not forced" });
      continue;
    }
    await btn.click();
    await page.waitForTimeout(700);
    await exhaust(page, { role, theme, route, tab: step, state: "v6-step" });
    if (step === "review") {
      for (const tabName of ["Finisaje", "Iluminare", "Montaj"]) {
        const t = page.getByRole("tab", { name: new RegExp(tabName, "i") }).or(page.getByRole("button", { name: new RegExp(tabName, "i") }));
        if (await t.count()) {
          await t.first().click();
          await page.waitForTimeout(400);
          await exhaust(page, { role, theme, route, tab: `review-${tabName}`, state: "v6-review-tab" });
        }
      }
    }
  }
}

async function captureOrders(theme, role) {
  const { ctx, page } = await openPage(browser, { theme, role, path: "/orders" });
  await exhaust(page, { role, theme, route: "/orders", tab: "default", state: "list" });
  const chips = page.locator("button").filter({ hasText: /Acceptat|locked|execu|Toate|all/i });
  if (await chips.count()) {
    await chips.first().click();
    await page.waitForTimeout(300);
    await exhaust(page, { role, theme, route: "/orders", tab: "status-filter", state: "filtered" });
  }
  const card = page.locator("[data-testid='orders-page']").locator("text=/ORD-|Q-/").first();
  if (await card.count()) {
    await card.click();
    await page.waitForTimeout(700);
    const dest = new URL(page.url()).pathname;
    edge({
      FROM_ROUTE: "/orders",
      FROM_ELEMENT: "order-card",
      CONTROL_LABEL: "select order",
      ROLE: role,
      TO_ROUTE: dest,
      ACTUAL_DESTINATION: dest,
      EXPECTED_PURPOSE: "order detail",
      HONESTY_STATUS: dest.startsWith("/orders") ? "GOOD_EDGE" : "SURPRISING_DESTINATION",
    });
    await exhaust(page, { role, theme, route: dest, tab: "order-detail", state: "detail" });
    const qlink = page.locator("a[href^='/quotes']").first();
    if (await qlink.count()) {
      const href = await qlink.getAttribute("href");
      edge({
        FROM_ROUTE: dest,
        FROM_ELEMENT: "quote-link",
        CONTROL_LABEL: await qlink.innerText(),
        ROLE: role,
        TO_ROUTE: href,
        ACTUAL_DESTINATION: href,
        EXPECTED_PURPOSE: "order → quote",
        HONESTY_STATUS: "GOOD_EDGE",
      });
    }
  } else {
    notReached.push({ route: "/orders/:id", blocker: "no selectable order row" });
  }
  await ctx.close();
}

async function captureClients(theme, role) {
  const { ctx, page } = await openPage(browser, { theme, role, path: "/clients" });
  await exhaust(page, { role, theme, route: "/clients", tab: "default", state: "list" });
  const row = page.locator("text=/SRL|SA|CLIENT|Client/i").first();
  if (await row.count()) {
    await row.click();
    await page.waitForTimeout(800);
    const dest = new URL(page.url()).pathname;
    edge({
      FROM_ROUTE: "/clients",
      FROM_ELEMENT: "client-row",
      CONTROL_LABEL: "client row",
      ROLE: role,
      TO_ROUTE: dest,
      ACTUAL_DESTINATION: dest,
      EXPECTED_PURPOSE: "client workspace",
      HONESTY_STATUS: dest.startsWith("/clients/") ? "GOOD_EDGE" : "SURPRISING_DESTINATION",
    });
    await exhaust(page, { role, theme, route: dest, tab: "overview", state: "workspace" });
    for (const tabName of ["Cereri", "Oferte", "Comenzi"]) {
      const t = page.getByRole("button", { name: tabName }).or(page.getByRole("tab", { name: tabName }));
      if (await t.count()) {
        const dis = await t.first().isDisabled().catch(() => false);
        if (dis) {
          notReached.push({ route: dest, tab: tabName, blocker: "tab disabled" });
          continue;
        }
        await t.first().click();
        await page.waitForTimeout(400);
        await exhaust(page, { role, theme, route: dest, tab: tabName, state: "client-tab" });
      }
    }
  } else {
    notReached.push({ route: "/clients/:name", blocker: "no client row clicked" });
  }
  await ctx.close();
}

async function observeQuotes(theme, role) {
  const { ctx, page } = await openPage(browser, { theme, role, path: "/quotes" });
  await page.locator("[data-testid='quotes-page'] span.font-mono").first().click().catch(() => {});
  await page.waitForTimeout(600);
  seq += 1;
  const dir = join(OUT, role, theme, "quotes-observe");
  mkdirSync(dir, { recursive: true });
  const file = `${String(seq).padStart(3, "0")}-quotes-observe-detail.png`;
  await page.screenshot({ path: join(dir, file) });
  results.push({
    role,
    theme,
    route: "/quotes",
    tab: "observe-detail",
    state: "wave1-reuse-edge-only",
    FULL_VERTICAL_SCROLL: "N/A",
    BOTTOM_REACHED: "NO",
    SCROLL_SEGMENT_COUNT: 1,
    segments: [{ file: `wave-2/runtime/screenshots/${role}/${theme}/quotes-observe/${file}` }],
    note: "Wave 1 already fully audited; edge inspect only",
  });
  const intake = page.getByTestId("quote-detail-intake-link");
  if (await intake.count()) {
    const href = await intake.getAttribute("href");
    edge({
      FROM_ROUTE: "/quotes",
      FROM_ELEMENT: "quote-detail-intake-link",
      CONTROL_LABEL: await intake.innerText(),
      ROLE: role,
      TO_ROUTE: href,
      ACTUAL_DESTINATION: href,
      EXPECTED_PURPOSE: "quote → intake V6",
      HONESTY_STATUS: (href || "").includes("intake-v6") ? "GOOD_EDGE" : "TECHNICAL_DESTINATION",
    });
  } else {
    notReached.push({ route: "/quotes", edge: "quote-detail-intake-link", blocker: "link absent on selected quote" });
  }
  const olink = page.locator("a[href^='/orders']").first();
  if (await olink.count()) {
    edge({
      FROM_ROUTE: "/quotes",
      FROM_ELEMENT: "orders-link",
      CONTROL_LABEL: await olink.innerText(),
      ROLE: role,
      TO_ROUTE: await olink.getAttribute("href"),
      ACTUAL_DESTINATION: await olink.getAttribute("href"),
      EXPECTED_PURPOSE: "quote → order",
      HONESTY_STATUS: "GOOD_EDGE",
    });
  }
  const clink = page.locator("a[href^='/clients']").first();
  if (!(await clink.count())) {
    edges.push({
      FROM_ROUTE: "/quotes",
      FROM_ELEMENT: "client-name",
      CONTROL_LABEL: "client (text)",
      ROLE: role,
      TO_ROUTE: "",
      ACTUAL_DESTINATION: "",
      EXPECTED_PURPOSE: "quote → client",
      HONESTY_STATUS: "DEAD_END",
      FOLLOWED: "NO",
      note: "client name is not a /clients link",
    });
  }
  await ctx.close();
}

try {
  for (const theme of ["light", "dark"]) {
    await captureIntake(theme, "admin");
    await captureOrders(theme, "admin");
    await captureClients(theme, "admin");
    await observeQuotes(theme, "admin");
  }
  await captureIntake("light", "sales");
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
      notReached,
    },
    null,
    2,
  ),
  "utf8",
);
console.log(
  `surfaces=${results.length} shots=${seq} scrollFail=${results.filter((r) => r.FULL_VERTICAL_SCROLL === "FAIL").length} edges=${edges.length} notReached=${notReached.length}`,
);
