/** Exhaust nested AppShell nav scroller (admin only; other roles fit). */
import { chromium } from "../../../frontend/node_modules/playwright/index.mjs";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const FE = "http://127.0.0.1:3000";
const OUT = join(__dirname, "wave-1", "screenshots", "scroll", "nav");
const results = [];

const browser = await chromium.launch({ headless: true });
for (const theme of ["light", "dark"]) {
  const ctx = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    colorScheme: theme === "dark" ? "dark" : "light",
  });
  await ctx.addInitScript(
    ({ t }) => {
      localStorage.setItem("access_token", "__DEV_BYPASS_TOKEN__");
      localStorage.setItem("token", "__DEV_BYPASS_TOKEN__");
      localStorage.setItem("workos-theme", t === "dark" ? "dark" : "light");
      sessionStorage.setItem("WORKOS_DEV_GUARD_BYPASS", "1");
      sessionStorage.setItem("workos-dev-role", "admin");
      document.documentElement.classList.remove("dark", "light");
      document.documentElement.classList.add(t === "dark" ? "dark" : "light");
    },
    { t: theme },
  );
  const page = await ctx.newPage();
  await page.goto(`${FE}/dashboard`, { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForTimeout(1200);
  const dir = join(OUT, theme);
  mkdirSync(dir, { recursive: true });

  await page.evaluate(() => {
    const nav = document.querySelector("[data-testid='workos-shell-nav']");
    if (nav) nav.scrollTop = 0;
  });
  const start = await page.evaluate(() => {
    const nav = document.querySelector("[data-testid='workos-shell-nav']");
    return {
      scrollTop: nav.scrollTop,
      clientHeight: nav.clientHeight,
      scrollHeight: nav.scrollHeight,
      max: nav.scrollHeight - nav.clientHeight,
    };
  });
  const segments = [];
  let idx = 0;
  const step = Math.max(120, start.clientHeight - 24);
  while (idx < 20) {
    const before = await page.evaluate(() => {
      const nav = document.querySelector("[data-testid='workos-shell-nav']");
      return { scrollTop: nav.scrollTop, max: nav.scrollHeight - nav.clientHeight };
    });
    const file = `nav-s${String(idx).padStart(2, "0")}-y${Math.round(before.scrollTop)}.png`;
    await page.screenshot({ path: join(dir, file) });
    segments.push({
      index: idx,
      scrollTop: before.scrollTop,
      file: `wave-1/screenshots/scroll/nav/${theme}/${file}`,
    });
    if (before.max <= 0 || before.scrollTop >= before.max - 1) break;
    await page.evaluate((y) => {
      const nav = document.querySelector("[data-testid='workos-shell-nav']");
      nav.scrollTop = y;
    }, Math.min(before.max, before.scrollTop + step));
    await page.waitForTimeout(150);
    const after = await page.evaluate(() => {
      const nav = document.querySelector("[data-testid='workos-shell-nav']");
      return { scrollTop: nav.scrollTop };
    });
    if (after.scrollTop <= before.scrollTop + 1) break;
    idx += 1;
  }
  const end = await page.evaluate(() => {
    const nav = document.querySelector("[data-testid='workos-shell-nav']");
    const before = nav.scrollTop;
    nav.scrollTop = nav.scrollHeight;
    return {
      before,
      scrollTop: nav.scrollTop,
      max: nav.scrollHeight - nav.clientHeight,
    };
  });
  const bottom = end.scrollTop >= end.max - 1;
  const pass = start.scrollTop === 0 && bottom;
  results.push({
    route: "/dashboard",
    role: "admin",
    theme,
    tab: "appshell-nav",
    container: "workos-shell-nav",
    SCROLL_START: start.scrollTop,
    SCROLL_END: end.scrollTop,
    SCROLL_MAX: end.max,
    BOTTOM_REACHED: bottom ? "YES" : "NO",
    NEW_CONTENT_AFTER_FINAL_SCROLL: end.scrollTop > end.before + 1 ? "YES" : "NO",
    SCROLL_SEGMENTS_CAPTURED: segments.length,
    FULL_VERTICAL_SCROLL: pass ? "PASS" : "FAIL",
    NESTED_SCROLL_CONTAINERS: ["workos-shell-nav"],
    segments,
  });
  console.log(theme, pass ? "PASS" : "FAIL", "segs", segments.length, "end", end.scrollTop, "/", end.max);
  await ctx.close();
}
await browser.close();
writeFileSync(
  join(__dirname, "wave-1", "nav-scroll-exhaust-log.json"),
  JSON.stringify({ results }, null, 2),
  "utf8",
);
