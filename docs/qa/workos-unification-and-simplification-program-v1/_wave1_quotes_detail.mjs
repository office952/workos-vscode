/** Follow-up: quote detail + overlays, no mutating submit. */
import { chromium } from "../../../frontend/node_modules/playwright/index.mjs";
import { mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const FE = "http://127.0.0.1:3000";
const OUT = join(__dirname, "wave-1", "screenshots", "admin");

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
  await page.goto(`${FE}/quotes`, { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForTimeout(1500);
  await page.locator("[data-testid='quotes-page'] span.font-mono").first().click();
  await page.waitForTimeout(800);
  const dir = join(OUT, theme);
  mkdirSync(dir, { recursive: true });
  await page.screenshot({ path: join(dir, `210-admin-${theme}-quotes-detail.png`) });

  const tech = page.getByText("Detalii tehnice — readiness / politică backend");
  if (await tech.count()) {
    await tech.first().click();
    await page.waitForTimeout(300);
    await page.screenshot({ path: join(dir, `211-admin-${theme}-quotes-tech-expand.png`) });
  }

  const send = page.getByTestId("quote-assisted-send-action");
  if ((await send.count()) && (await send.isEnabled())) {
    await send.click();
    await page.waitForTimeout(400);
    await page.screenshot({ path: join(dir, `212-admin-${theme}-quotes-send-dialog.png`) });
    await page.keyboard.press("Escape");
  } else {
    await page.screenshot({ path: join(dir, `212-admin-${theme}-quotes-send-disabled.png`) });
  }

  const rev = page.getByTestId("quote-revision-action");
  if ((await rev.count()) && (await rev.isEnabled())) {
    await rev.click();
    await page.waitForTimeout(400);
    await page.screenshot({ path: join(dir, `213-admin-${theme}-quotes-revision-dialog.png`) });
    await page.keyboard.press("Escape");
  }

  console.log(theme, page.url(), "sendEnabled", await send.isEnabled().catch(() => false));
  await ctx.close();
}
await browser.close();
