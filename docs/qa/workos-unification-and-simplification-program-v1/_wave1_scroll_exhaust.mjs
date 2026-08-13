/**
 * Wave 1 — full vertical scroll exhaustion on the real shell scroller.
 * Primary container: main.overflow-auto (AppShell). window scroll is invalid.
 */
import { chromium } from "../../../frontend/node_modules/playwright/index.mjs";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const FE = process.env.WORKOS_FE_URL || "http://127.0.0.1:3000";
const OUT = join(__dirname, "wave-1", "screenshots", "scroll");
const VIEWPORT = { width: 1440, height: 900 };

const SURFACES = [
  { role: "admin", path: "/dashboard", tab: "default" },
  { role: "admin", path: "/quotes", tab: "default" },
  { role: "admin", path: "/quotes", tab: "Ciornă", filter: "Ciornă" },
  { role: "admin", path: "/quotes", tab: "Tarifat", filter: "Tarifat" },
  { role: "admin", path: "/quotes", tab: "Acceptat", filter: "Acceptat" },
  { role: "admin", path: "/quotes", tab: "quote-selected" },
  { role: "admin", path: "/shop-floor", tab: "default" },
  { role: "sales", path: "/quotes", tab: "default" },
  { role: "operator", path: "/shop-floor", tab: "default" },
];

function discoverScrollers() {
  const nodes = [...document.querySelectorAll("main, nav, aside, [data-testid], div")];
  const seen = new Set();
  const out = [];
  for (const el of nodes) {
    const style = getComputedStyle(el);
    const oy = style.overflowY;
    if (oy !== "auto" && oy !== "scroll") continue;
    if (el.scrollHeight <= el.clientHeight + 2) continue;
    if (seen.has(el)) continue;
    seen.add(el);
    out.push({
      key:
        el.getAttribute("data-testid") ||
        `${el.tagName.toLowerCase()}.${(el.className || "").toString().split(" ").slice(0, 3).join(".")}`,
      tag: el.tagName.toLowerCase(),
      testid: el.getAttribute("data-testid") || "",
      className: (el.className || "").toString().slice(0, 120),
      scrollTop: el.scrollTop,
      clientHeight: el.clientHeight,
      scrollHeight: el.scrollHeight,
      max: Math.max(0, el.scrollHeight - el.clientHeight),
      isMain: el.tagName === "MAIN",
    });
  }
  return out;
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
  return {
    scrollTop: el.scrollTop,
    clientHeight: el.clientHeight,
    scrollHeight: el.scrollHeight,
    max: Math.max(0, el.scrollHeight - el.clientHeight),
  };
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
      document.documentElement.setAttribute("data-theme", t === "dark" ? "dark" : "light");
    },
    { t: theme, r: role },
  );
  const page = await ctx.newPage();
  page.setDefaultTimeout(20000);
  await page.goto(`${FE}${path}`, { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForTimeout(1400);
  const bypass = page.getByRole("button", { name: /Bypass temporar preview/i });
  if (await bypass.count()) {
    await bypass.click();
    await page.waitForTimeout(1200);
  }
  return { ctx, page };
}

async function exhaustMain(page, { role, theme, path, tab }) {
  await page.evaluate(setScrollerTop, 0);
  await page.waitForTimeout(150);
  const start = await page.evaluate(scrollerMetrics);
  const nested = await page.evaluate(discoverScrollers);
  const dir = join(OUT, role, theme, path.replace(/\//g, "_") || "root", tab.replace(/\s+/g, "_"));
  mkdirSync(dir, { recursive: true });

  const segments = [];
  let y = 0;
  let idx = 0;
  const step = Math.max(200, start.clientHeight - 48);
  const maxGuard = 40;

  while (idx < maxGuard) {
    const before = await page.evaluate(scrollerMetrics);
    const file = `s${String(idx).padStart(2, "0")}-y${Math.round(before.scrollTop)}.png`;
    await page.screenshot({ path: join(dir, file) });
    segments.push({
      index: idx,
      scrollTop: before.scrollTop,
      file: `wave-1/screenshots/scroll/${role}/${theme}/${path.replace(/\//g, "_") || "root"}/${tab.replace(/\s+/g, "_")}/${file}`,
    });

    if (before.max <= 0 || before.scrollTop >= before.max - 1) break;

    y = Math.min(before.max, before.scrollTop + step);
    await page.evaluate(setScrollerTop, y);
    await page.waitForTimeout(180);
    const after = await page.evaluate(scrollerMetrics);
    if (after.scrollTop <= before.scrollTop + 1) break;
    idx += 1;
  }

  const atMax = await page.evaluate(scrollerMetrics);
  const beforeFinal = atMax.scrollTop;
  await page.evaluate((m) => {
    const main = document.querySelector("[data-testid='workos-desktop-shell'] main");
    if (main) main.scrollTop = m + 2000;
  }, atMax.max);
  await page.waitForTimeout(150);
  const afterFinal = await page.evaluate(scrollerMetrics);
  const newAfterFinal = afterFinal.scrollTop > beforeFinal + 1 || afterFinal.scrollHeight > atMax.scrollHeight + 2;

  const bottomReached = afterFinal.max <= 0 || afterFinal.scrollTop >= afterFinal.max - 1;
  const pass =
    start.scrollTop === 0 &&
    bottomReached &&
    !newAfterFinal &&
    segments.length >= 1;

  return {
    route: path,
    role,
    theme,
    tab,
    container: start.used,
    SCROLL_START: start.scrollTop,
    SCROLL_END: afterFinal.scrollTop,
    SCROLL_MAX: afterFinal.max,
    clientHeight: afterFinal.clientHeight,
    scrollHeight: afterFinal.scrollHeight,
    BOTTOM_REACHED: bottomReached ? "YES" : "NO",
    NEW_CONTENT_AFTER_FINAL_SCROLL: newAfterFinal ? "YES" : "NO",
    SCROLL_SEGMENTS_CAPTURED: segments.length,
    FULL_VERTICAL_SCROLL: pass ? "PASS" : "FAIL",
    NESTED_SCROLL_CONTAINERS: nested.map((n) => `${n.key} max=${n.max}`),
    segments,
  };
}

const results = [];
const browser = await chromium.launch({ headless: true });
try {
  for (const theme of ["light", "dark"]) {
    for (const surface of SURFACES) {
      const { ctx, page } = await openPage(browser, {
        theme,
        role: surface.role,
        path: surface.path,
      });
      if (surface.filter) {
        const btn = page.getByRole("button", { name: new RegExp(surface.filter, "i") });
        if (await btn.count()) {
          await btn.first().click();
          await page.waitForTimeout(400);
        }
      }
      if (surface.tab === "quote-selected") {
        const card = page.locator("[data-testid='quotes-page'] span.font-mono").first();
        if (await card.count()) {
          await card.click();
          await page.waitForTimeout(600);
        }
      }
      const row = await exhaustMain(page, {
        role: surface.role,
        theme,
        path: surface.path,
        tab: surface.tab,
      });
      results.push(row);
      console.log(
        `${surface.role} ${theme} ${surface.path} ${surface.tab} ${row.FULL_VERTICAL_SCROLL} segs=${row.SCROLL_SEGMENTS_CAPTURED} end=${row.SCROLL_END}/${row.SCROLL_MAX} nested=${row.NESTED_SCROLL_CONTAINERS.length}`,
      );
      await ctx.close();
    }
  }
} finally {
  await browser.close();
}

const logPath = join(__dirname, "wave-1", "scroll-exhaust-log.json");
writeFileSync(logPath, JSON.stringify({ fe: FE, viewport: VIEWPORT, results }, null, 2), "utf8");
const fail = results.filter((r) => r.FULL_VERTICAL_SCROLL !== "PASS").length;
console.log(`surfaces=${results.length} fail=${fail} log=${logPath}`);
