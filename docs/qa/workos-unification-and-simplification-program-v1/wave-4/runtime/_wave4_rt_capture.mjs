/**
 * Wave 4 RT — Product System / Modules / Governance. READ-ONLY.
 * Never click: save, activate, publish, create product, template activation, Product Truth confirm.
 */
import { chromium } from "../../../../../frontend/node_modules/playwright/index.mjs";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const FE = process.env.WORKOS_FE_URL || "http://127.0.0.1:3000";
const OUT = join(__dirname, "screenshots");
const VIEWPORT = { width: 1440, height: 900 };
const LETTERS = "/product-system/products/TPL-VOLUMETRIC-LETTERS_v2";
const ACM = "/product-system/products/TPL-ACM-BOXED-MOUNTING-SUPPORT_v1";

const results = [];
const edges = [];
const roleMatrix = [];
const notReached = [];
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
      file: `wave-4/runtime/screenshots/${meta.role}/${meta.theme}/${slug(meta.route)}/${slug(meta.tab || "default")}/${file}`,
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
    (path.includes("/:") && landed.startsWith(path.split("/:")[0]));
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
  const n = Math.min(await summaries.count(), 10);
  for (let i = 0; i < n; i += 1) {
    const s = summaries.nth(i);
    const text = ((await s.innerText()) || "").trim();
    if (/salveaz|activeaz|public|creeaz|confirm/i.test(text)) continue;
    await s.click().catch(() => {});
    await page.waitForTimeout(120);
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

async function clickSafeTabs(page, names) {
  for (const name of names) {
    const tab = page.getByRole("tab", { name: new RegExp(name, "i") }).first();
    const btn = page.getByRole("button", { name: new RegExp(`^${name}`, "i") }).first();
    const loc = (await tab.count()) ? tab : btn;
    if (await loc.count()) {
      const label = ((await loc.innerText()) || name).trim();
      if (/salveaz|activeaz|public|creeaz|confirm/i.test(label)) continue;
      await loc.click().catch(() => {});
      await page.waitForTimeout(400);
    }
  }
}

async function main() {
  const browser = await chromium.launch({ headless: true });

  for (const theme of ["light", "dark"]) {
    const opened = await capturePath(browser, theme, "admin", "/product-system/products", true, "library");
    if (opened.allowed) {
      const { page, ctx } = opened;
      const card = page.locator("a[href*='/product-system/products/TPL-'], button, [data-testid*='template']").filter({ hasText: /VOLUMETRIC|Litere|Letters/i }).first();
      if (await card.count()) {
        await card.click().catch(() => {});
        await page.waitForTimeout(800);
        edges.push({
          FROM: "/product-system/products",
          CONTROL: "product card",
          TO: new URL(page.url()).pathname,
          HONESTY: "GOOD_EDGE",
        });
        await exhaust(page, { role: "admin", theme, route: new URL(page.url()).pathname, tab: "letters-detail" });
      }
      await ctx.close();
    }

    await (async () => {
      const o = await capturePath(browser, theme, "admin", LETTERS, true, "letters-direct");
      if (!o.allowed) return;
      const { page, ctx } = o;
      const face = page.getByRole("link", { name: /față|fata|vizual/i }).first();
      if (await face.count()) {
        await face.click().catch(() => {});
        await page.waitForTimeout(700);
        const dest = new URL(page.url()).pathname;
        edges.push({ FROM: LETTERS, CONTROL: "structure față", TO: dest, HONESTY: dest.includes("structure") ? "GOOD_EDGE" : "SURPRISING" });
        await exhaust(page, { role: "admin", theme, route: dest, tab: "structure-face" });
      }
      await ctx.close();
    })();

    if (theme === "light") {
      await capturePath(browser, theme, "admin", ACM, true, "acm-direct").then((o) => o.allowed && o.ctx.close());
      for (const p of [
        "/product-system/components",
        "/product-system/operations",
        "/product-system/blueprint-dossier",
        "/product-system/output-blocks-preview",
      ]) {
        const o = await capturePath(browser, theme, "admin", p, true, "default");
        if (o.allowed) await o.ctx.close();
      }
    }
  }

  for (const theme of ["light", "dark"]) {
    const o = await capturePath(browser, theme, "admin", "/modules", true, "harta");
    if (o.allowed) {
      const { page, ctx } = o;
      await clickSafeTabs(page, ["Contracte", "Stare", "Surse", "Harta"]);
      await expandReadOnly(page);
      await exhaust(page, { role: "admin", theme, route: "/modules", tab: "tabs-expanded" });
      await ctx.close();
    }

    const g = await capturePath(browser, theme, "admin", "/governance", true, "ownership");
    if (g.allowed) {
      const { page, ctx } = g;
      await clickSafeTabs(page, [
        "Cine deține",
        "Harta limitelor",
        "Fluxuri",
        "Autoritatea",
        "Surse de adevăr",
        "Owner gates",
        "Reguli de protecție",
        "Catalog",
        "Reguli de adevăr",
      ]);
      await expandReadOnly(page);
      await exhaust(page, { role: "admin", theme, route: "/governance", tab: "tabs-expanded" });
      await ctx.close();
    }
  }

  for (const role of ["manager", "sales"]) {
    const o = await capturePath(browser, "light", role, "/product-system/products", true, "library");
    if (o.allowed) await o.ctx.close();
    for (const p of ["/modules", "/governance"]) {
      const d = await capturePath(browser, "light", role, p, false, "denied");
      if (d.allowed) await d.ctx.close();
    }
  }

  {
    const o = await capturePath(browser, "light", "operator", "/product-system/products", false, "denied");
    if (o.allowed) await o.ctx.close();
  }

  await browser.close();
  const fail = results.filter((r) => r.FULL_VERTICAL_SCROLL === "FAIL").length;
  writeFileSync(
    join(__dirname, "rt-capture-log.json"),
    JSON.stringify({ results, edges, roleMatrix, notReached, fail, shots: seq }, null, 2),
  );
  console.log(JSON.stringify({ surfaces: results.length, shots: seq, fail, roles: roleMatrix.length, edges: edges.length }, null, 2));
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
