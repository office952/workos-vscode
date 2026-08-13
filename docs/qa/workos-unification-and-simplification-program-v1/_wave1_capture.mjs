/**
 * Wave 1 live capture — evidence helper, not product code.
 * Reuses the Owner live stack on :3000. Does not mutate Owner dev.db.
 */
import { chromium } from "../../../frontend/node_modules/playwright/index.mjs";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const FE = process.env.WORKOS_FE_URL || "http://127.0.0.1:3000";
const OUT = join(__dirname, "wave-1", "screenshots");
const VIEWPORT = { width: 1440, height: 900 };

const ADMIN_NAV = [
  ["Cereri", "/intake"],
  ["Produse", "/product-system/products"],
  ["Oferte", "/quotes"],
  ["Comenzi", "/orders"],
  ["Atelier", "/shop-floor"],
  ["Planificare", "/execution"],
  ["Rulări utilaj", "/execution/machine-runs"],
  ["Ops-Graph", "/execution/ops-graph"],
  ["Acțiune task (legacy)", "/operator"],
  ["Stații (legacy)", "/tablet"],
  ["Angajați", "/employees"],
  ["Pontaj", "/attendance"],
  ["Evidență HR", "/employees-records"],
  ["Utilaje", "/utilaje"],
  ["Inventar", "/inventory"],
  ["Prețuri", "/inventory/pricing"],
  ["Clienți", "/clients"],
  ["Colaboratori", "/colaboratori"],
  ["Documente", "/documents"],
  ["Control producție", "/dashboard"],
  ["Rapoarte", "/reports"],
  ["Plăți", "/employee-payments"],
  ["Avansuri", "/employee-advances"],
  ["Harta", "/modules"],
  ["Guvernanță", "/governance"],
  ["Setări", "/settings"],
  ["Demo Commercial Spine", "/demo/commercial-spine"],
  ["Demo Volumetric Preview", "/demo/volumetric-letter-preview"],
  ["Blueprint Dossier", "/product-system/blueprint-dossier"],
  ["Rapoarte operaționale", "/reports/operational"],
];

const SALES_NAV = [
  ["Cereri", "/intake"],
  ["Produse", "/product-system/products"],
  ["Oferte", "/quotes"],
  ["Comenzi", "/orders"],
  ["Planificare", "/execution"],
  ["Inventar", "/inventory"],
  ["Clienți", "/clients"],
  ["Documente", "/documents"],
  ["Control producție", "/dashboard"],
  ["Rapoarte", "/reports"],
];

const OPERATOR_NAV = [
  ["Atelier", "/shop-floor"],
  ["Rulări utilaj", "/execution/machine-runs"],
  ["Acțiune task (legacy)", "/operator"],
  ["Stații (legacy)", "/tablet"],
  ["Utilaje", "/utilaje"],
  ["Inventar", "/inventory"],
];

const ROLE_HOME = { admin: "/dashboard", sales: "/quotes", operator: "/shop-floor" };
const ROLE_NAV = { admin: ADMIN_NAV, sales: SALES_NAV, operator: OPERATOR_NAV };

const manifest = [];
const graph = [];
const interactions = [];
let seq = 0;

function nextName(parts) {
  seq += 1;
  const n = String(seq).padStart(3, "0");
  return `${n}-${parts.join("-").replace(/[^a-zA-Z0-9_-]+/g, "_")}.png`;
}

async function shot(page, meta) {
  const file = nextName([
    meta.role,
    meta.theme,
    meta.route.replace(/^\//, "").replace(/\//g, "_") || "root",
    meta.tag,
  ]);
  const dir = join(OUT, meta.role, meta.theme);
  mkdirSync(dir, { recursive: true });
  const path = join(dir, file);
  await page.screenshot({ path, fullPage: Boolean(meta.fullPage) });
  const row = {
    route: meta.route,
    role: meta.role,
    theme: meta.theme,
    viewport: `${VIEWPORT.width}x${VIEWPORT.height}`,
    scroll: meta.scroll || "top",
    tab: meta.tab || "none",
    expandable: meta.expandable || "none",
    overlay: meta.overlay || "none",
    linkDest: meta.linkDest || "",
    state: meta.state || "default",
    file: `wave-1/screenshots/${meta.role}/${meta.theme}/${file}`,
    coverage: "COVERED",
  };
  manifest.push(row);
  return row;
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
  await page.waitForTimeout(1200);
  const bypass = page.getByRole("button", { name: /Bypass temporar preview/i });
  if (await bypass.count()) {
    await bypass.click();
    await page.waitForTimeout(1500);
  }
  return { ctx, page };
}

async function scrollSegments(page, meta) {
  await page.evaluate(() => window.scrollTo(0, 0));
  await shot(page, { ...meta, tag: "top", scroll: "top" });
  const heights = await page.evaluate(() => ({
    scroll: document.scrollingElement?.scrollHeight || document.body.scrollHeight,
    inner: window.innerHeight,
  }));
  if (heights.scroll > heights.inner + 80) {
    await page.evaluate(() => window.scrollTo(0, Math.floor(window.innerHeight * 0.85)));
    await page.waitForTimeout(250);
    await shot(page, { ...meta, tag: "mid", scroll: "mid" });
  }
  if (heights.scroll > heights.inner * 1.8) {
    await page.evaluate(() => window.scrollTo(0, document.scrollingElement.scrollHeight));
    await page.waitForTimeout(250);
    await shot(page, { ...meta, tag: "bottom", scroll: "bottom" });
  }
  await page.evaluate(() => window.scrollTo(0, 0));
}

async function traverseShell(page, meta) {
  const userBtn = page.getByLabel(/Cont utilizator/i);
  if (await userBtn.count()) {
    await userBtn.click();
    await page.waitForTimeout(300);
    await shot(page, { ...meta, tag: "user-menu", overlay: "user-menu-open" });
    await page.keyboard.press("Escape");
    await page.waitForTimeout(200);
  }
  const collapse = page.getByTestId("workos-nav-collapse");
  if (await collapse.count()) {
    await collapse.click();
    await page.waitForTimeout(300);
    await shot(page, { ...meta, tag: "nav-collapsed", overlay: "nav-collapsed" });
    await collapse.click();
    await page.waitForTimeout(300);
  }
}

async function traverseDashboard(page, meta) {
  await scrollSegments(page, { ...meta, route: "/dashboard" });
  const moreRisks = page.getByRole("button", { name: /Vezi toate/i });
  if (await moreRisks.count()) {
    await moreRisks.click();
    await page.waitForTimeout(300);
    await shot(page, {
      ...meta,
      route: "/dashboard",
      tag: "risks-expanded",
      expandable: "riscuri-livrare",
    });
  } else {
    interactions.push({
      route: "/dashboard",
      item: "riscuri-expand",
      coverage: "NOT_APPLICABLE",
      note: "fewer than 5 risky jobs or control absent",
    });
  }
}

async function traverseQuotes(page, meta) {
  await scrollSegments(page, { ...meta, route: "/quotes" });
  const search = page.getByTestId("quotes-search-input");
  if (await search.count()) {
    await search.click();
    await shot(page, { ...meta, route: "/quotes", tag: "search-focus", state: "search-focus" });
  }
  const statusBtn = page.locator("button").filter({ hasText: /draft|priced|sent|Toate|all/i }).first();
  if (await statusBtn.count()) {
    await statusBtn.click();
    await page.waitForTimeout(300);
    await shot(page, { ...meta, route: "/quotes", tag: "status-filter", tab: "status-filter" });
  }
  const firstRow = page.locator("[data-testid='quotes-page'] a, [data-testid='quotes-page'] tr, [data-testid='quotes-page'] button").filter({ hasText: /Q-|OF-|draft|priced/i }).first();
  if (await firstRow.count()) {
    await firstRow.click();
    await page.waitForTimeout(800);
    const dest = new URL(page.url()).pathname;
    await scrollSegments(page, { ...meta, route: dest, tag: "quote-detail", tab: "quote-detail" });
    const send = page.getByRole("button", { name: /Trimite|Send/i });
    if (await send.count()) {
      await send.first().click();
      await page.waitForTimeout(400);
      await shot(page, {
        ...meta,
        route: dest,
        tag: "send-dialog",
        overlay: "QuoteSendDialog",
        state: "modal-open-no-submit",
      });
      await page.keyboard.press("Escape");
      await page.waitForTimeout(200);
    }
    const rev = page.getByRole("button", { name: /Revizie|Revision/i });
    if (await rev.count()) {
      await rev.first().click();
      await page.waitForTimeout(400);
      await shot(page, {
        ...meta,
        route: dest,
        tag: "revision-dialog",
        overlay: "QuoteRevisionDialog",
        state: "modal-open-no-submit",
      });
      await page.keyboard.press("Escape");
      await page.waitForTimeout(200);
    }
  } else {
    await shot(page, { ...meta, route: "/quotes", tag: "empty-or-no-row", state: "empty-or-no-selectable-row" });
  }
}

async function traverseShopFloor(page, meta) {
  await scrollSegments(page, { ...meta, route: "/shop-floor" });
  const refresh = page.getByRole("button", { name: /Reîmprospăt|Refresh/i });
  if (await refresh.count()) {
    await refresh.first().click();
    await page.waitForTimeout(400);
    await shot(page, { ...meta, route: "/shop-floor", tag: "after-refresh", state: "refreshed" });
  }
}

async function followNav(page, meta, label, declared) {
  const link = page.locator("[data-testid='workos-shell-nav'] a, [data-testid='workos-sidebar'] a").filter({ hasText: label }).first();
  const visible = (await link.count()) > 0 && (await link.isVisible().catch(() => false));
  if (!visible) {
    graph.push({
      FROM_ROUTE: meta.route,
      ROLE: meta.role,
      CONTROL_LABEL: label,
      TO_ROUTE: "",
      DESTINATION_STATUS: "control not visible",
      EXPECTED_USER_PURPOSE: declared,
      HONESTY_STATUS: "unknown",
      FOLLOWED: "NO",
      note: "NOT_APPLICABLE or hidden for this role/session",
    });
    return;
  }
  await link.click();
  await page.waitForTimeout(900);
  const actual = new URL(page.url()).pathname;
  const title = (await page.locator("h1").first().innerText().catch(() => "")).slice(0, 80);
  await shot(page, {
    ...meta,
    route: actual,
    tag: `nav-${label}`,
    linkDest: actual,
    state: "nav-landing",
  });
  graph.push({
    FROM_ROUTE: meta.route,
    ROLE: meta.role,
    CONTROL_LABEL: label,
    TO_ROUTE: actual,
    DESTINATION_STATUS: title || actual,
    EXPECTED_USER_PURPOSE: declared,
    HONESTY_STATUS: "see CHARTER / nav def",
    FOLLOWED: "YES",
  });
}

const browser = await chromium.launch({ headless: true });

try {
  for (const role of ["admin", "sales", "operator"]) {
    for (const theme of ["light", "dark"]) {
      const home = ROLE_HOME[role];
      const { ctx, page } = await openPage(browser, { theme, role, path: home });
      const meta = { role, theme, route: new URL(page.url()).pathname };
      const shellRole = await page.locator("[data-shell-role]").getAttribute("data-shell-role").catch(() => null);
      interactions.push({
        role,
        theme,
        home,
        actualPath: meta.route,
        shellRole,
        bodyPreview: (await page.locator("body").innerText()).replace(/\s+/g, " ").slice(0, 280),
      });

      await traverseShell(page, meta);
      if (home === "/dashboard") await traverseDashboard(page, meta);
      if (home === "/quotes") await traverseQuotes(page, meta);
      if (home === "/shop-floor") await traverseShopFloor(page, meta);

      if (role === "admin" && home !== "/quotes") {
        const { ctx: qctx, page: qpage } = await openPage(browser, { theme, role, path: "/quotes" });
        await traverseQuotes(qpage, { role, theme, route: "/quotes" });
        await qctx.close();
      }
      if (role === "admin" && home !== "/shop-floor") {
        const { ctx: sctx, page: spage } = await openPage(browser, { theme, role, path: "/shop-floor" });
        await traverseShopFloor(spage, { role, theme, route: "/shop-floor" });
        await sctx.close();
      }

      for (const [label, declared] of ROLE_NAV[role]) {
        await followNav(page, { ...meta, route: home }, label, declared);
      }
      await ctx.close();
    }
  }
} finally {
  await browser.close();
}

const logPath = join(__dirname, "wave-1", "capture-log.json");
mkdirSync(join(__dirname, "wave-1"), { recursive: true });
writeFileSync(
  logPath,
  JSON.stringify({ fe: FE, seq, manifest, graph, interactions }, null, 2),
  "utf8",
);
console.log(`shots=${manifest.length} edges=${graph.filter((g) => g.FOLLOWED === "YES").length} log=${logPath}`);
