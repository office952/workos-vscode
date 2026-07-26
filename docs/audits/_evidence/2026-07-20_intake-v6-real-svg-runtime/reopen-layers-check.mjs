import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";
import fs from "node:fs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(path.join(__dirname, "../../../../frontend/package.json"));
const { chromium } = require("playwright");

const cases = [
  { id: "319c706e-fd7d-407a-9903-67f5c560085b", dir: "case1-acm-segmentat" },
  { id: "ebfed730-eaf9-4e90-ad9e-aa949a061c7d", dir: "case2-gradi-curat" },
];

async function main() {
  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  await ctx.addInitScript(() => {
    try {
      sessionStorage.setItem("WORKOS_DEV_GUARD_BYPASS", "1");
    } catch {
      /* ignore */
    }
  });
  const page = await ctx.newPage();
  const out = [];

  for (const c of cases) {
    await page.goto(`http://127.0.0.1:3000/intake-v6/${c.id}/operator`, {
      waitUntil: "domcontentloaded",
      timeout: 120_000,
    });
    await page.waitForTimeout(2500);
    await page.getByTestId("intake-v6-progress-step-layers").click().catch(() => {});
    await page.waitForTimeout(1500);
    const chip = await page
      .getByTestId("intake-v6-file-confirm-chip")
      .textContent()
      .catch(() => null);
    const layers = await page.locator('[data-testid^="intake-v6-layer-row-"]').count();
    const dims = await page.evaluate(() => {
      const t = document.body.innerText || "";
      const m = t.match(/(\d[\d.,]*)\s*mm\s*[×x]\s*(\d[\d.,]*)\s*mm/i);
      return m ? `${m[1]} x ${m[2]}` : null;
    });
    const dir = path.join(__dirname, c.dir);
    await page.screenshot({ path: path.join(dir, "15-layers-after-reopen-1440x900.png") });

    await page.getByTestId("intake-v6-progress-step-review").click().catch(() => {});
    await page.waitForTimeout(1200);
    const problemBtn = page.locator("text=/!\\s*\\d+\\s*probleme/i").first();
    let problemDrawer = [];
    if (await problemBtn.isVisible().catch(() => false)) {
      await problemBtn.click().catch(() => {});
      await page.waitForTimeout(800);
      await page.screenshot({ path: path.join(dir, "16-problems-drawer-1440x900.png") });
      problemDrawer = await page.evaluate(() =>
        Array.from(document.querySelectorAll("li, p, button, [role='alert']"))
          .map((e) => (e.textContent || "").replace(/\s+/g, " ").trim())
          .filter((t) => t.length > 8 && t.length < 220)
          .filter((t) => /bloc|lips|necesit|confirm|finisaj|compoz|problem|segment/i.test(t))
          .slice(0, 40),
      );
    }

    // Montaj segment wording
    const montaj = page.getByTestId("intake-v6-review-tab-montaj");
    if (await montaj.isVisible().catch(() => false)) {
      await montaj.click();
      await page.waitForTimeout(800);
      await page.screenshot({ path: path.join(dir, "17-montaj-reopen-1440x900.png") });
    }
    const montajText = await page.evaluate(() => {
      const t = document.body.innerText || "";
      const hits = [];
      for (const re of [
        /segment[^\n]{0,80}/gi,
        /Alucobond[^\n]{0,80}/gi,
        /fundal[^\n]{0,80}/gi,
        /Logo[^\n]{0,60}/gi,
      ]) {
        const m = t.match(re);
        if (m) hits.push(...m.slice(0, 5));
      }
      return [...new Set(hits)].slice(0, 20);
    });

    out.push({
      id: c.id,
      chip: chip?.trim() || null,
      layers,
      dims,
      problemDrawer,
      montajText,
    });
  }

  fs.writeFileSync(path.join(__dirname, "reopen-layers-check.json"), JSON.stringify(out, null, 2));
  console.log(JSON.stringify(out, null, 2));
  await browser.close();
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
