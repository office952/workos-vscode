/**
 * Wave 5 gap closure RT — /employees-records/:id only.
 * READ-ONLY. Never click save / create / add document / apply / generate / record / cancel.
 */
import { chromium } from "../../../../../frontend/node_modules/playwright/index.mjs";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const FE = process.env.WORKOS_FE_URL || "http://127.0.0.1:3000";
const OUT = join(__dirname, "screenshots-gap-closure");
const VIEWPORT = { width: 1440, height: 900 };
const TABS = ["Profil", "Documente", "Medicina muncii", "Alerte"];

const results = [];
const roleMatrix = [];
const notReached = [];
const navProof = {};
let seq = 0;
let employeeId = null;

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
      file: `wave-5/runtime/screenshots-gap-closure/${meta.role}/${meta.theme}/${slug(meta.route)}/${slug(meta.tab || "default")}/${file}`,
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
  const stillOn =
    landed === path ||
    landed.startsWith(`${path}/`) ||
    (path.includes("/employees-records/") && /^\/employees-records\/[^/]+$/.test(landed));
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

async function clickSafeTabs(page) {
  for (const name of TABS) {
    const loc = page.getByRole("button", { name: new RegExp(`^${name}`, "i") }).first();
    if (await loc.count()) {
      const label = ((await loc.innerText()) || name).trim();
      if (/salveaz|creeaz|adaug|șterge|sterge|aplic|genereaz|înregistreaz|inregistreaz|anuleaz/i.test(label)) {
        continue;
      }
      await loc.click().catch(() => {});
      await page.waitForTimeout(400);
      await exhaust(page, {
        role: await page.evaluate(() => sessionStorage.getItem("workos-dev-role") || "admin"),
        theme: await page.evaluate(() =>
          document.documentElement.classList.contains("dark") ? "dark" : "light",
        ),
        route: new URL(page.url()).pathname,
        tab: name,
      });
    }
  }
}

async function captureDenied(browser, theme, role, path) {
  const { ctx, page } = await openPage(browser, { theme, role, path });
  const allowed = await recordRole(page, role, theme, path, false);
  if (allowed) {
    notReached.push({ route: path, role, theme, blocker: "expected denial but page stayed" });
  }
  seq += 1;
  const dir = join(OUT, role, theme, slug(path), "denied");
  mkdirSync(dir, { recursive: true });
  await page.screenshot({ path: join(dir, `${String(seq).padStart(3, "0")}-denied.png`) });
  await ctx.close();
}

async function captureDetail(browser, theme, role, path, tabPrefix) {
  const { ctx, page } = await openPage(browser, { theme, role, path });
  const allowed = await recordRole(page, role, theme, path, true);
  if (!allowed) {
    notReached.push({ route: path, role, theme, blocker: `ROLE_ALLOWED=NO landing=${new URL(page.url()).pathname}` });
    seq += 1;
    const dir = join(OUT, role, theme, slug(path), "denied");
    mkdirSync(dir, { recursive: true });
    await page.screenshot({ path: join(dir, `${String(seq).padStart(3, "0")}-denied.png`) });
    await ctx.close();
    return;
  }
  const demoBadge = await page.locator("text=/^DEMO$/").count();
  const confidential = await page.locator("text=/Confidențial/i").count();
  await exhaust(page, { role, theme, route: new URL(page.url()).pathname, tab: `${tabPrefix}-landing` });
  await clickSafeTabs(page);
  results[results.length - 1] = {
    ...results[results.length - 1],
    DEMO_BADGE: demoBadge > 0 ? "YES" : "NO",
    CONFIDENTIAL_LABEL: confidential > 0 ? "YES" : "NO",
  };
  await ctx.close();
}

async function main() {
  const browser = await chromium.launch({ headless: true });

  const { ctx, page } = await openPage(browser, { theme: "light", role: "admin", path: "/employees-records" });
  await page.waitForTimeout(800);
  const hrefCount = await page.locator("a[href*='/employees-records/']").count();
  const rowButtons = page.locator("button").filter({ hasText: /Activ|Inactiv|Plecat/ });
  const rowCount = await rowButtons.count();
  navProof.listPath = "/employees-records";
  navProof.anchorHrefCount = hrefCount;
  navProof.rowButtonCount = rowCount;
  navProof.affordance = hrefCount === 0 && rowCount > 0 ? "BUTTON_ONCLICK_NOT_ANCHOR" : hrefCount > 0 ? "ANCHOR" : "NONE";
  seq += 1;
  const listDir = join(OUT, "admin", "light", "_employees-records-nav-proof", "list");
  mkdirSync(listDir, { recursive: true });
  await page.screenshot({ path: join(listDir, `${String(seq).padStart(3, "0")}-list-before-row-click.png`) });
  if (rowCount === 0) {
    navProof.rowClick = "NO_ROW";
    notReached.push({ route: "/employees-records/:id", role: "admin", theme: "light", blocker: "no employee row button" });
    await ctx.close();
  } else {
    await rowButtons.first().click();
    await page.waitForTimeout(1200);
    const landed = new URL(page.url()).pathname;
    const match = landed.match(/^\/employees-records\/([^/]+)$/);
    navProof.rowClick = match ? "REACHED" : `LANDED_${landed}`;
    navProof.employeeId = match ? match[1] : null;
    employeeId = match ? match[1] : null;
    await recordRole(page, "admin", "light", landed, true);
    const demoBadge = await page.locator("text=/^DEMO$/").count();
    await exhaust(page, { role: "admin", theme: "light", route: landed, tab: "row-click-landing" });
    await clickSafeTabs(page);
    results[results.length - 1] = {
      ...results[results.length - 1],
      DEMO_BADGE: demoBadge > 0 ? "YES" : "NO",
      ENTRY: "ROW_BUTTON_CLICK",
    };
    await ctx.close();
  }

  if (!employeeId) {
    writeFileSync(
      join(__dirname, "rt-gap-closure-log.json"),
      JSON.stringify({ navProof, results, roleMatrix, notReached, seq, error: "no employee id" }, null, 2),
    );
    await browser.close();
    process.exit(1);
  }

  const detail = `/employees-records/${employeeId}`;
  navProof.deepLink = detail;
  await captureDetail(browser, "dark", "admin", detail, "deeplink");
  await captureDetail(browser, "light", "manager", detail, "deeplink");
  await captureDenied(browser, "light", "sales", detail);
  await captureDenied(browser, "light", "operator", detail);

  const scrollFails = results.filter((r) => r.FULL_VERTICAL_SCROLL === "FAIL").length;
  const roleMismatch = roleMatrix.filter((r) => r.MATCH !== "YES").length;
  const log = {
    task: "WAVE_5_EVIDENCE_GAP_CLOSURE_V1",
    mutations: 0,
    surfaces: results.length,
    shots: seq,
    FULL_SCROLL_FAILURES: scrollFails,
    ROLE_MATCH_FAILURES: roleMismatch,
    navProof,
    results,
    roleMatrix,
    notReached,
  };
  writeFileSync(join(__dirname, "rt-gap-closure-log.json"), JSON.stringify(log, null, 2));
  await browser.close();
  console.log(JSON.stringify({
    surfaces: results.length,
    shots: seq,
    FULL_SCROLL_FAILURES: scrollFails,
    ROLE_MATCH_FAILURES: roleMismatch,
    employeeId,
    affordance: navProof.affordance,
    rowClick: navProof.rowClick,
  }));
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
