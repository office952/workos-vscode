/**
 * Wave 2 gap closure — read-only. No create/save/handoff/convert.
 * Does not overwrite Wave 2 seq 001–106. New shots start at 200.
 * Proves Straturi + Panou; sales light/dark; back-nav; hover/focus; client stubs.
 */
import { chromium } from "../../../../../frontend/node_modules/playwright/index.mjs";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const FE = process.env.WORKOS_FE_URL || "http://127.0.0.1:3000";
const OUT = join(__dirname, "screenshots");
const VIEWPORT = { width: 1440, height: 900 };
const V6_PATH = "/intake-v6/IR-MSRB28PU/operator";

const results = [];
const proofs = [];
const backNav = [];
const hoverFocus = [];
const roleMatrix = [];
const notReached = [];
let seq = 199;

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
    gap_closure: true,
  };
  results.push(row);
  return row;
}

async function shot(page, meta, label) {
  seq += 1;
  const dir = join(OUT, meta.role, meta.theme, slug(meta.route), slug(meta.tab || "sample"));
  mkdirSync(dir, { recursive: true });
  const file = `${String(seq).padStart(3, "0")}-${slug(label)}.png`;
  await page.screenshot({ path: join(dir, file) });
  return `wave-2/runtime/screenshots/${meta.role}/${meta.theme}/${slug(meta.route)}/${slug(meta.tab || "sample")}/${file}`;
}

async function readStepProof(page) {
  return page.evaluate(() => {
    const layers = document.querySelector("[data-testid='intake-v6-progress-step-layers']");
    const review = document.querySelector("[data-testid='intake-v6-progress-step-review']");
    const body = document.body.innerText || "";
    const pas = (body.match(/Pasul\s+\d+\s+din\s+3[^\n]*/i) || [""])[0];
    return {
      layersAriaCurrent: layers?.getAttribute("aria-current") || null,
      layersDisabled: layers ? layers.disabled : null,
      reviewAriaCurrent: review?.getAttribute("aria-current") || null,
      pasLabel: pas,
      hasStraturiWord: /Straturi/i.test(body),
      hasConfigurareWord: /Configurare/i.test(body),
      layersPanel: Boolean(document.querySelector("[data-testid='intake-v6-layers-operator-panel'], [data-testid='intake-v6-layer-table'], [data-testid='intake-v6-layers-metrics-strip']")),
    };
  });
}

async function gotoStraturi(page) {
  const btn = page.getByTestId("intake-v6-progress-step-layers");
  if (!(await btn.count())) {
    return { ok: false, blocker: "intake-v6-progress-step-layers absent" };
  }
  if (await btn.isDisabled()) {
    return { ok: false, blocker: "layers step disabled — not forced" };
  }
  await btn.click();
  await page.waitForTimeout(900);
  let proof = await readStepProof(page);
  if (proof.layersAriaCurrent !== "step" || !proof.layersPanel) {
    await btn.click();
    await page.waitForTimeout(900);
    proof = await readStepProof(page);
  }
  const ok = proof.layersAriaCurrent === "step" && (proof.layersPanel || /Pasul 1/i.test(proof.pasLabel));
  return { ok, proof };
}

async function gotoPanou(page) {
  const review = page.getByTestId("intake-v6-progress-step-review");
  if (await review.count()) {
    if (await review.isDisabled()) {
      return { ok: false, blocker: "review step disabled — not forced" };
    }
    await review.click();
    await page.waitForTimeout(700);
  }
  const panou = page.getByTestId("intake-v6-review-tab-panou_carcasa");
  if (!(await panou.count())) {
    return { ok: false, blocker: "intake-v6-review-tab-panou_carcasa absent on this workspace" };
  }
  await panou.click();
  await page.waitForTimeout(600);
  const selected = await panou.getAttribute("aria-selected");
  const label = (await panou.innerText()).replace(/\s+/g, " ").trim();
  return { ok: selected === "true", selected, label };
}

async function expandReadOnly(page) {
  const opened = [];
  const summaries = page.locator("summary");
  const n = Math.min(await summaries.count(), 6);
  for (let i = 0; i < n; i += 1) {
    const s = summaries.nth(i);
    const text = ((await s.innerText()) || "").trim();
    if (/salveaz|confirm|persist|import|încarc/i.test(text)) continue;
    await s.click().catch(() => {});
    opened.push(text.slice(0, 80));
    await page.waitForTimeout(200);
  }
  return opened;
}

async function navPresence(page, label) {
  const item = page.locator("nav, [data-testid='workos-shell-nav']").getByText(label, { exact: true });
  return (await item.count()) > 0;
}

async function captureV6Gaps(browser, theme, role) {
  const { ctx, page } = await openPage(browser, { theme, role, path: V6_PATH });
  const dest = new URL(page.url()).pathname;
  if (dest.endsWith("/intake-v6/operator") || dest === "/intake-v6/operator") {
    notReached.push({
      route: V6_PATH,
      role,
      theme,
      blocker: "landed on bootstrap operator — aborted to avoid create",
      MUTATION_REQUIRED: "YES",
    });
    await ctx.close();
    return;
  }

  const straturi = await gotoStraturi(page);
  proofs.push({ kind: "STRATURI", role, theme, route: dest, ...straturi });
  if (!straturi.ok) {
    notReached.push({
      route: dest,
      tab: "straturi",
      role,
      theme,
      blocker: straturi.blocker || JSON.stringify(straturi.proof),
    });
  } else {
    const opened = await expandReadOnly(page);
    await exhaust(page, {
      role,
      theme,
      route: dest,
      tab: "straturi",
      state: "v6-step-straturi-proven",
      ACTUAL_STEP: "Straturi",
      expandables: opened,
    });
  }

  const panou = await gotoPanou(page);
  proofs.push({ kind: "PANOU", role, theme, route: dest, ...panou });
  if (!panou.ok) {
    notReached.push({
      route: dest,
      tab: "panou_carcasa",
      role,
      theme,
      blocker: panou.blocker || `aria-selected=${panou.selected}`,
    });
  } else {
    const opened = await expandReadOnly(page);
    await exhaust(page, {
      role,
      theme,
      route: dest,
      tab: "review-Panou-carcasa",
      state: "v6-review-tab-panou",
      expandables: opened,
    });
  }
  await ctx.close();
}

async function captureRoleSurface(browser, theme, role, path, expectTestId, label) {
  const { ctx, page } = await openPage(browser, { theme, role, path });
  const url = new URL(page.url());
  const navYes = await navPresence(page, label);
  const pageYes = expectTestId ? (await page.getByTestId(expectTestId).count()) > 0 : url.pathname.startsWith(path);
  const allowed = pageYes || url.pathname.startsWith(path.split("/:")[0]);
  roleMatrix.push({
    role,
    theme,
    route: path,
    ROLE_ALLOWED: allowed ? "YES" : "NO",
    SOURCE: "runtime",
    NAV_VISIBLE: navYes ? "YES" : "NO",
    LANDING: url.pathname,
    PAGE_TESTID: expectTestId,
    PAGE_PRESENT: pageYes,
  });
  if (!allowed) {
    notReached.push({
      route: path,
      role,
      theme,
      blocker: `RBAC/runtime: landed ${url.pathname}; nav=${navYes} page=${pageYes}`,
      SOURCE: "RBAC+runtime",
    });
    await ctx.close();
    return { ctx: null, page: null, allowed: false };
  }
  return { ctx, page, allowed: true };
}

async function captureOrders(browser, theme, role) {
  const opened = await captureRoleSurface(browser, theme, role, "/orders", "orders-page", "Comenzi");
  if (!opened.allowed) return;
  const { ctx, page } = opened;
  await exhaust(page, { role, theme, route: "/orders", tab: "default", state: "list" });
  const card = page.locator("[data-testid='orders-page']").locator("text=/ORD-|Q-/").first();
  if (await card.count()) {
    await card.click();
    await page.waitForTimeout(700);
    const dest = new URL(page.url()).pathname;
    await exhaust(page, { role, theme, route: dest, tab: "order-detail", state: "detail" });
  } else {
    notReached.push({ route: "/orders/:id", role, theme, blocker: "no selectable order row" });
  }
  await ctx.close();
}

async function captureClients(browser, theme, role) {
  const opened = await captureRoleSurface(browser, theme, role, "/clients", null, "Clienți");
  if (!opened.allowed) return;
  const { ctx, page } = opened;
  await exhaust(page, { role, theme, route: "/clients", tab: "default", state: "list" });
  const row = page.locator("text=/SRL|SA|CLIENT|Client/i").first();
  if (!(await row.count())) {
    notReached.push({ route: "/clients/:name", role, theme, blocker: "no client row" });
    await ctx.close();
    return;
  }
  await row.click();
  await page.waitForTimeout(800);
  const dest = new URL(page.url()).pathname;
  await exhaust(page, { role, theme, route: dest, tab: "overview", state: "workspace" });
  for (const tabName of ["Cereri", "Oferte", "Comenzi", "Facturi", "Documente", "Note", "Timeline"]) {
    const t = page.getByRole("button", { name: tabName }).or(page.getByRole("tab", { name: tabName }));
    if (!(await t.count())) {
      notReached.push({ route: dest, tab: tabName, role, theme, blocker: "tab control absent" });
      continue;
    }
    if (await t.first().isDisabled().catch(() => false)) {
      notReached.push({
        route: dest,
        tab: tabName,
        role,
        theme,
        blocker: "tab disabled",
        CLASS: "INACTIVE",
      });
      continue;
    }
    await t.first().click();
    await page.waitForTimeout(350);
    await exhaust(page, { role, theme, route: dest, tab: tabName, state: "client-tab" });
  }
  await ctx.close();
}

async function captureIntakeRole(browser, theme, role) {
  const opened = await captureRoleSurface(browser, theme, role, "/intake", null, "Cereri");
  if (!opened.allowed) return;
  const { ctx, page } = opened;
  await exhaust(page, { role, theme, route: "/intake", tab: "default", state: "list" });
  await ctx.close();
}

async function captureBackNav(browser, theme) {
  const cases = [
    { start: "/intake", drill: async (page) => {
      const edit = page.getByTestId("work-intake-primary-edit");
      const row = page.locator("[data-testid^='work-intake-row-']").first();
      if (await row.count()) await row.click();
      await page.waitForTimeout(400);
      if (await edit.count()) {
        await edit.click();
        await page.waitForTimeout(1200);
      }
    }, expectBack: "/intake" },
    { start: "/orders", drill: async (page) => {
      const card = page.locator("[data-testid='orders-page']").locator("text=/ORD-|Q-/").first();
      if (await card.count()) {
        await card.click();
        await page.waitForTimeout(700);
      }
    }, expectBack: "/orders" },
    { start: "/clients", drill: async (page) => {
      const row = page.locator("text=/SRL|SA|CLIENT|Client/i").first();
      if (await row.count()) {
        await row.click();
        await page.waitForTimeout(800);
      }
    }, expectBack: "/clients" },
  ];

  for (const c of cases) {
    const { ctx, page } = await openPage(browser, { theme, role: "admin", path: c.start });
    await page.evaluate(setScrollerTop, 80);
    const beforeScroll = await page.evaluate(scrollerMetrics);
    const from = new URL(page.url()).pathname;
    await c.drill(page);
    const to = new URL(page.url()).pathname;
    await page.goBack();
    await page.waitForTimeout(800);
    const back = new URL(page.url()).pathname;
    const afterScroll = await page.evaluate(scrollerMetrics);
    const rec = {
      FROM_ROUTE: from,
      TO_ROUTE: to,
      BACK_ROUTE: back,
      FILTER_PRESERVED: "UNKNOWN",
      SELECTION_PRESERVED: back === c.expectBack && to !== back ? "UNKNOWN" : back === c.expectBack ? "PARTIAL" : "NO",
      SCROLL_PRESERVED: Math.abs(afterScroll.scrollTop - beforeScroll.scrollTop) <= 8 ? "YES" : "NO",
      CONTEXT_PRESERVED: back === c.expectBack || back.startsWith(c.expectBack) ? "YES" : "NO",
      theme,
      role: "admin",
    };
    backNav.push(rec);
    seq += 1;
    const dir = join(OUT, "admin", theme, "back-nav", slug(c.start));
    mkdirSync(dir, { recursive: true });
    const file = `${String(seq).padStart(3, "0")}-after-back.png`;
    await page.screenshot({ path: join(dir, file) });
    rec.SCREENSHOT = `wave-2/runtime/screenshots/admin/${theme}/back-nav/${slug(c.start)}/${file}`;
    await ctx.close();
  }
}

async function captureHoverFocus(browser, theme) {
  const { ctx, page } = await openPage(browser, { theme, role: "admin", path: "/intake" });
  const samples = [];

  async function sample(kind, locator, extra = {}) {
    if (!(await locator.count())) {
      hoverFocus.push({ theme, kind, HOVER_STATE: "ABSENT", FOCUS_STATE: "ABSENT", ...extra });
      return;
    }
    const el = locator.first();
    await el.scrollIntoViewIfNeeded().catch(() => {});
    await el.hover().catch(() => {});
    await page.waitForTimeout(180);
    const hoverFile = await shot(page, { role: "admin", theme, route: "/intake", tab: "hover-focus" }, `hover-${kind}`);
    await el.focus().catch(() => {});
    await page.waitForTimeout(180);
    const focusFile = await shot(page, { role: "admin", theme, route: "/intake", tab: "hover-focus" }, `focus-${kind}`);
    const box = await el.evaluate((node) => {
      const s = getComputedStyle(node);
      return {
        outline: s.outline,
        outlineWidth: s.outlineWidth,
        boxShadow: s.boxShadow,
        disabled: node.disabled === true,
      };
    });
    const rec = {
      theme,
      kind,
      HOVER_STATE: "CAPTURED",
      FOCUS_STATE: "CAPTURED",
      VISIBLE_FOCUS: box.outlineWidth !== "0px" || (box.boxShadow && box.boxShadow !== "none") ? "YES" : "WEAK_OR_NONE",
      THEME_PARITY: "PENDING_COMPARE",
      ISSUE: null,
      hoverFile,
      focusFile,
      ...extra,
    };
    hoverFocus.push(rec);
    samples.push(rec);
  }

  await sample("nav-item", page.locator("[data-testid='workos-shell-nav'] a, nav a").filter({ hasText: /Cereri/ }).first(), { primitive: "nav item" });
  await sample("list-row", page.locator("[data-testid^='work-intake-row-']").first(), { primitive: "table/list row" });
  await sample("search-input", page.locator("input[type='search'], input[placeholder*='Caut']").first(), { primitive: "select/input" });
  const row = page.locator("[data-testid^='work-intake-row-']").first();
  if (await row.count()) {
    await row.click();
    await page.waitForTimeout(400);
  }
  await sample("primary-cta", page.getByTestId("work-intake-primary-edit"), { primitive: "primary CTA" });
  await sample("secondary-button", page.getByRole("button", { name: /Cerere Nou|Filtr|Reîmprosp/i }).first(), { primitive: "secondary button" });

  await page.goto(`${FE}${V6_PATH}`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(1200);
  const review = page.getByTestId("intake-v6-progress-step-review");
  if (await review.count() && !(await review.isDisabled())) {
    await review.click();
    await page.waitForTimeout(500);
  }
  await sample("tab", page.getByTestId("intake-v6-review-tab-finisaje"), { primitive: "tab" });
  const confirm = page.getByTestId("intake-v6-progress-step-confirm");
  if (await confirm.count() && !(await confirm.isDisabled())) {
    await confirm.click();
    await page.waitForTimeout(500);
  }
  const disabled = page.getByRole("button", { name: /Continuă către ofertă|Continuă la ofertă/i });
  await sample("disabled-cta", disabled, { primitive: "disabled control" });

  await ctx.close();
}

const browser = await chromium.launch({ headless: true });
try {
  for (const theme of ["light", "dark"]) {
    for (const role of ["admin", "sales"]) {
      await captureIntakeRole(browser, theme, role);
      await captureV6Gaps(browser, theme, role);
      await captureOrders(browser, theme, role);
      await captureClients(browser, theme, role);
    }
    await captureBackNav(browser, theme);
    await captureHoverFocus(browser, theme);
  }
} finally {
  await browser.close();
}

const logPath = join(__dirname, "rt-gap-closure-log.json");
writeFileSync(
  logPath,
  JSON.stringify(
    {
      fe: FE,
      seq,
      surfaces: results.length,
      scrollFail: results.filter((r) => r.FULL_VERTICAL_SCROLL === "FAIL").length,
      results,
      proofs,
      backNav,
      hoverFocus,
      roleMatrix,
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
      shots: seq - 199,
      scrollFail: results.filter((r) => r.FULL_VERTICAL_SCROLL === "FAIL").length,
      proofs: proofs.length,
      backNav: backNav.length,
      hoverFocus: hoverFocus.length,
      roleMatrix: roleMatrix.length,
      notReached: notReached.length,
    },
    null,
    2,
  ),
);
