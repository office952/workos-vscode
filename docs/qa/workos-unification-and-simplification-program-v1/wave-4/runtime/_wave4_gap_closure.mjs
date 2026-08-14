/**
 * Wave 4 gap closure RT — missing workshops, planned 4/6, sales/manager dark.
 * READ-ONLY. Never click save / activate / publish / create / confirm.
 */
import { chromium } from "../../../../../frontend/node_modules/playwright/index.mjs";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const FE = process.env.WORKOS_FE_URL || "http://127.0.0.1:3000";
const OUT = join(__dirname, "screenshots-gap-closure");
const VIEWPORT = { width: 1440, height: 900 };
const LETTERS = "TPL-VOLUMETRIC-LETTERS_v2";
const ACM = "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1";

const WORKSHOPS = [
  `/product-system/products/${LETTERS}/structure/vizual-fata`,
  `/product-system/products/${LETTERS}/structure/volum-aluminiu`,
  `/product-system/products/${LETTERS}/structure/capac-spate`,
  `/product-system/products/${LETTERS}/structure/sistem-led`,
  `/product-system/products/${LETTERS}/structure/conexiune-litere-acm-preturi`,
  `/product-system/products/${LETTERS}/structure/composer-litere-acm`,
  `/product-system/products/${ACM}/structure/corp-casetat`,
  `/product-system/products/${ACM}/structure/structura-metalica`,
];

const PLANNED_MISSING = [
  "/product-system/resources",
  "/product-system/dependencies",
  "/product-system/validation",
  "/product-system/advanced",
];

const results = [];
const roleMatrix = [];
const notReached = [];
const apiProbe = {};
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
  await page.waitForTimeout(80);
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
      file: `wave-4/runtime/screenshots-gap-closure/${meta.role}/${meta.theme}/${slug(meta.route)}/${slug(meta.tab || "default")}/${file}`,
    });
    if (before.max <= 0 || before.scrollTop >= before.max - 1) break;
    await page.evaluate(setScrollerTop, Math.min(before.max, before.scrollTop + step));
    await page.waitForTimeout(120);
    const after = await page.evaluate(scrollerMetrics);
    if (after.scrollTop <= before.scrollTop + 1) break;
    idx += 1;
  }
  const atMax = await page.evaluate(scrollerMetrics);
  await page.evaluate((m) => {
    const main = document.querySelector("[data-testid='workos-desktop-shell'] main");
    if (main) main.scrollTop = m + 4000;
  }, atMax.max);
  await page.waitForTimeout(80);
  const afterFinal = await page.evaluate(scrollerMetrics);
  const newAfter = afterFinal.scrollTop > atMax.scrollTop + 1 || afterFinal.scrollHeight > atMax.scrollHeight + 2;
  const bottom = afterFinal.max <= 0 || afterFinal.scrollTop >= afterFinal.max - 1;
  results.push({
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
  });
}

async function recordRole(page, role, theme, path, expectedAllowed) {
  const url = new URL(page.url());
  const landed = url.pathname;
  const deniedUi = await page.locator("text=/nu ai acces|access denied|nepermis/i").count();
  const stillOn = landed === path || landed.startsWith(`${path}/`) || path.startsWith(landed);
  const allowed = stillOn && deniedUi === 0;
  roleMatrix.push({
    role,
    theme,
    route: path,
    ROLE_ALLOWED: allowed ? "YES" : "NO",
    LANDING: landed,
    EXPECTED: expectedAllowed ? "YES" : "NO",
    MATCH: allowed === expectedAllowed ? "YES" : "NO",
  });
  return allowed;
}

async function expandReadOnly(page) {
  const summaries = page.locator("summary");
  const n = Math.min(await summaries.count(), 12);
  for (let i = 0; i < n; i += 1) {
    const s = summaries.nth(i);
    const text = ((await s.innerText()) || "").trim();
    if (/salveaz|activeaz|public|creeaz|confirm/i.test(text)) continue;
    await s.click().catch(() => {});
    await page.waitForTimeout(100);
  }
}

async function capturePath(browser, theme, role, path, expectedAllowed, tab = "default") {
  const { ctx, page } = await openPage(browser, { theme, role, path });
  const allowed = await recordRole(page, role, theme, path, expectedAllowed);
  if (!allowed) {
    notReached.push({ route: path, role, theme, blocker: `ROLE_ALLOWED=NO landing=${new URL(page.url()).pathname}` });
    seq += 1;
    const dir = join(OUT, role, theme, slug(path), "denied");
    mkdirSync(dir, { recursive: true });
    await page.screenshot({ path: join(dir, `${String(seq).padStart(3, "0")}-denied.png`) });
    await ctx.close();
    return { allowed: false };
  }
  await expandReadOnly(page);
  await exhaust(page, { role, theme, route: new URL(page.url()).pathname, tab });
  return { allowed: true, page, ctx };
}

async function main() {
  const browser = await chromium.launch({ headless: true });

  for (const theme of ["light", "dark"]) {
    for (const path of WORKSHOPS) {
      const o = await capturePath(browser, theme, "admin", path, true, "workshop");
      if (o.allowed) await o.ctx.close();
    }
    for (const path of PLANNED_MISSING) {
      const o = await capturePath(browser, theme, "admin", path, true, "planned");
      if (o.allowed) await o.ctx.close();
    }
  }

  const redirect = await capturePath(
    browser,
    "light",
    "admin",
    `/product-system/products/${ACM}/structure/fata-panou`,
    true,
    "acm-legacy-redirect",
  );
  if (redirect.allowed) await redirect.ctx.close();

  const legacy = await capturePath(
    browser,
    "light",
    "admin",
    `/product-system/products/${LETTERS}?ps_legacy=1`,
    true,
    "legacy-editor",
  );
  if (legacy.allowed) await legacy.ctx.close();

  for (const role of ["manager", "sales"]) {
    const o = await capturePath(browser, "dark", role, "/product-system/products", true, "library-dark");
    if (o.allowed) await o.ctx.close();
  }

  {
    const { ctx, page } = await openPage(browser, { theme: "light", role: "admin", path: "/operator" });
    apiProbe.operatorTasks = await page.evaluate(async () => {
      const res = await fetch("/api/v1/operator/tasks", { credentials: "include" });
      const data = await res.json().catch(() => null);
      const tasks = Array.isArray(data) ? data : data?.tasks || data?.items || [];
      const for973024 = tasks.filter((t) => String(t.order_id) === "973024" || String(t.orderId) === "973024");
      return {
        http: res.status,
        total: tasks.length,
        count973024: for973024.length,
        sampleIds: for973024.slice(0, 8).map((t) => t.task_id || t.taskId || t.id),
        sampleNames: for973024.slice(0, 8).map((t) => t.name || t.technical_name || t.title),
      };
    });
    await ctx.close();
  }

  await browser.close();
  const fail = results.filter((r) => r.FULL_VERTICAL_SCROLL === "FAIL").length;
  writeFileSync(
    join(__dirname, "rt-gap-closure-log.json"),
    JSON.stringify({ results, roleMatrix, notReached, apiProbe, fail, shots: seq, mutations: 0 }, null, 2),
  );
  console.log(JSON.stringify({ surfaces: results.length, shots: seq, fail, roles: roleMatrix.length, api: apiProbe }, null, 2));
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
